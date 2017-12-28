#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from bs4 import BeautifulSoup
from bs4.element import Tag
from requests import Session
from requests.adapters import HTTPAdapter

session = Session()
session.mount('https://', HTTPAdapter(max_retries=3))
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)'
                  ' Chrome/33.0.1750.146 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'utf-8',
    'Accept-Language': 'zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3',
    'Connection': 'keep-alive'
}


class Dependency:

    def __init__(self, group_id, artifact_id, version, scope, optional):
        self.__group_id = group_id
        self.__artifact_id = artifact_id
        self.__version = version
        self.__scope = scope
        self.__optional = optional

    @property
    def group_id(self):
        return self.__group_id

    @property
    def artifact_id(self):
        return self.__artifact_id

    @property
    def version(self):
        return self.__version

    @property
    def scope(self):
        return self.__scope

    @property
    def optional(self):
        return self.__optional

    def __str__(self):
        return json.dumps({
            'group_id': self.__group_id,
            'artifact_id': self.__artifact_id,
            'version': self.__version,
            'scope': self.__scope,
            'optional': self.__optional
        })

    __repr__ = __str__


class Developer:
    def __init__(self, name, email, dev_id, roles, organization):
        self.__name = name
        self.__email = email
        self.__dev_id = dev_id
        self.__roles = roles
        self.__organization = organization

    @property
    def name(self):
        return self.__name

    @property
    def email(self):
        return self.__email

    @property
    def dev_id(self):
        return self.__dev_id

    @property
    def roles(self):
        return self.__roles

    @property
    def organization(self):
        return self.__organization

    def __str__(self):
        return json.dumps({
            'name': self.__name,
            'email': self.__email,
            'dev_id': self.__dev_id,
            'roles': self.__roles,
            'organization': self.__organization
        })


class Artifact:
    __url = 'https://mvnrepository.com/artifact/{0}/{1}/{2}'

    def __init__(self, location):
        self.__group_id = location[0]
        self.__artifact_id = location[1]
        self.__version = location[2]
        self.__dependencies = []
        self.__developers = []
        self.__name = None
        self.__description = None
        self.__licenses = []
        self.__organization = None
        self.__home_page = None
        self.__date = None
        self.__init(location)

    def __init(self, location):
        r = session.get(self.__url.format(location[0], location[1], location[2]), headers=headers)
        dom = BeautifulSoup(r.text, 'html5lib')
        version_sections = dom.select('div.version-section')
        self.__analyse_version_sections(version_sections)
        im = dom.select('#maincontent > .im')[0]
        self.__analyse_im(im)
        detail = dom.select('#maincontent > .grid')[0]
        self.__init_detail(detail)

    def __analyse_im(self, im):
        name = im.select('.im-header > .im-title > a')[0].text.strip()
        description = im.select('.im-description')[0].text.strip()
        self.__name = name
        self.__description = description

    def __init_detail(self, table):
        for tr in table.tbody:
            key = tr.th.text.strip()
            value = tr.td.text.strip()
            if key == 'Organization':
                self.__organization = value
            elif key == 'HomePage':
                self.__home_page = value
            elif key == 'Date':
                self.__date = value
            elif key == 'License':
                for lic in tr.td:
                        self.__licenses.append(lic.text.strip())

    def __analyse_version_sections(self, version_sections):
        for v in version_sections:
            if v.h2 is None:
                continue
            title = v.h2.text
            if title.startswith('Compile Dependencies'):
                self.__init_dependencies(v.div.table, 'compile')
            elif title.startswith('Managed Dependencies'):
                self.__init_dependencies(v.div.table, 'managed')
            elif title.startswith('Provided Dependencies'):
                self.__init_dependencies(v.div.table, 'provided')
            elif title.startswith('Test Dependencies'):
                self.__init_dependencies(v.div.table, 'test')
            elif title.startswith('Runtime Dependencies'):
                self.__init_dependencies(v.div.table, 'runtime')
            elif title.startswith('System Dependencies'):
                self.__init_dependencies(v.div.table, 'system')
            elif title.startswith('Import Dependencies'):
                self.__init_dependencies(v.div.table, 'import')
            elif title.startswith('Developers'):
                self.__init_developers(v.div.table)
            elif title.startswith('Licenses') or title.startswith('Mailing Lists'):
                pass

    def __init_developers(self, table):
        trs = table.tbody
        if trs is None:
            return
        for tr in trs:
            tds = tr.select('td')
            name = tds[0].text.strip()
            email = tds[1].text.strip()
            dev_id = tds[2].text.strip()
            roles = tds[3].text.strip()
            organization = tds[4].text.strip()
            developer = Developer(name, email, dev_id, roles, organization)
            self.__developers.append(developer)

    def __init_dependencies(self, table, scope):
        trs = table.tbody
        if trs is None:
            return
        for tr in trs:
            tds = tr.select('td')
            temp = tds[2].text.split('»')
            dependency_group_id = temp[0].strip()
            dependency_artifact_id = temp[1].strip()
            optional = True if tds[2].span else False
            dependency_version = tds[3]
            if dependency_version:
                dependency_version = dependency_version.text.strip()
            dependency = Dependency(dependency_group_id, dependency_artifact_id, dependency_version, scope, optional)
            self.__dependencies.append(dependency)

    @property
    def dependencies(self):
        return self.__dependencies

    @property
    def name(self):
        return self.__name

    @property
    def description(self):
        return self.__description

    @property
    def licenses(self):
        return self.__licenses

    @property
    def organization(self):
        return self.__organization

    @property
    def home_page(self):
        return self.__home_page

    @property
    def date(self):
        return self.__date

    @property
    def developers(self):
        return self.__developers

    @property
    def group_id(self):
        return self.__group_id

    @property
    def artifact_id(self):
        return self.__artifact_id

    @property
    def version(self):
        return self.__version

    def __str__(self):
        dev = []
        for d in self.__developers:
            dev.append({
                'name': d.name,
                'email': d.email,
                'dev_id': d.dev_id,
                'roles': d.roles,
                'organization': d.organization
            })
        dep = []
        for d2 in self.__dependencies:
            dep.append({
                'group_id': d2.group_id,
                'artifact_id': d2.artifact_id,
                'version': d2.version,
                'scope': d2.scope,
                'optional': d2.optional
            })
        return json.dumps({
            'group_id': self.group_id,
            'artifact_id': self.artifact_id,
            'version': self.version,
            'name': self.name,
            'description': self.description,
            'organization': self.organization,
            'home_page': self.home_page,
            'date': self.date,
            'licenses': self.licenses,
            'developers': dev,
            'dependencies': dep
        })
