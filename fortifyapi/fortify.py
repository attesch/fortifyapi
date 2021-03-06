#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Brandon Spruth (brandon.spruth2@target.com), Jim Nelson (jim.nelson2@target.com)"
__copyright__ = "(C) 2017 Target Brands, Inc."
__contributors__ = ["Brandon Spruth", "Jim Nelson", "Matthew Dunaj"]
__status__ = "Production"
__license__ = "MIT"

import urllib
import urllib3
import json
import ntpath
import requests
import requests.auth
import requests.exceptions
import requests.packages.urllib3
from . import __version__ as version


class FortifyApi(object):
    def __init__(self, host, username=None, password=None, token=None, verify_ssl=True, timeout=60, user_agent=None,
                 client_version='17.10.0158'):

        self.host = host
        self.username = username
        self.password = password
        self.token = token
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.client_version = client_version

        if not user_agent:
            self.user_agent = 'fortify_api/' + version
        else:
            self.user_agent = user_agent

        if not self.verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Set auth_type based on what's been provided
        if username is not None:
            self.auth_type = 'basic'
        elif token is not None:
            self.auth_type = 'token'
        else:
            self.auth_type = 'unauthenticated'

    @staticmethod
    def __formatted_application_version_payload__(project_name, project_id, version_name, issue_template_id,
                                                  description):
        """
        :param project_name: Project name
        :param project_id: Project ID
        :param version_name: Version name
        :param issue_template_id: Issue template ID
        :param description: Project version description
        :return:
        """
        json_application_version = dict(name='', description='', active=True, committed=True, issueTemplateId='',
                                        project={
                                            'name': '',
                                            'description': '',
                                            'issueTemplateId': '',
                                            'id': ''
                                        })

        json_application_version['project']['issueTemplateId'] = issue_template_id
        json_application_version['project']['name'] = project_name
        json_application_version['project']['id'] = project_id
        json_application_version['issueTemplateId'] = issue_template_id
        json_application_version['name'] = version_name
        json_application_version['description'] = description

        return json_application_version

    @staticmethod
    def __formatted_new_application_version_payload__(project_name, version_name, issue_template_id,
                                                  description):
        """
        :param project_name: Project name
        :param version_name: Version name
        :param issue_template_id: Issue template ID
        :param description: Project version description
        :return:
        """
        json_application_version = dict(name='', description='', active=True, committed=True, issueTemplateId='',
                                        project={
                                            'name': '',
                                            'description': '',
                                            'issueTemplateId': ''
                                        })

        json_application_version['project']['issueTemplateId'] = issue_template_id
        json_application_version['project']['name'] = project_name
        json_application_version['issueTemplateId'] = issue_template_id
        json_application_version['name'] = version_name
        json_application_version['description'] = description

        return json_application_version

    def add_project_version_attribute(self, project_version_id, attribute_definition_id, value,
                                      values, guid=None):
        """
        :param project_version_id: Project version id
        :param attribute_definition_id: Attribute definition ID
        :param guid: GUID
        :param value: Value
        :param values: Values
        :return: A response object containing the result of the attribute change
        """
        project_version_attribute = dict(attributeDefinitionId="", guid="", value="", values=values)

        project_version_attribute['attributeDefinitionId'] = attribute_definition_id
        project_version_attribute['guid'] = guid
        project_version_attribute['value'] = value
        project_version_attribute['values'] = values

        url = '/ssc/api/v1/projectVersions/' + str(project_version_id) + '/attributes'
        data = json.dumps(project_version_attribute)
        return self._request('POST', url, data=data)

    def commit_project_version(self, project_version_id):
        """
        Set the commit attribute of the specified project version to true
        :param project_version_id:
        :return: A response object containing the result of the attribute change
        """
        project_version_attribute = {
            "committed": True
        }

        url = '/ssc/api/v1/projectVersions/' + str(project_version_id)
        data = json.dumps(project_version_attribute)
        return self._request('PUT', url, data=data)

    def create_project_version(self, project_name, project_id, project_template, version_name, description):
        """
        :param project_name: Project name
        :param project_id: Project ID
        :param project_template: Project template
        :param version_name: Version name
        :param description: Description of project version
        :return: A response object containing the created project version
        """
        issue_template = self.get_issue_template(project_template_id=project_template)
        issue_template_id = issue_template.data['data'][0]['_href']
        # SSC API returns the full url for the issue template, strip away just the ID
        issue_template_id = issue_template_id.rsplit('/', 1)[1]
        data = json.dumps(self.__formatted_application_version_payload__(project_name=project_name,
                                                                         project_id=project_id,
                                                                         version_name=version_name,
                                                                         issue_template_id=issue_template_id,
                                                                         description=description))
        url = '/ssc/api/v1/projectVersions'
        return self._request('POST', url, data=data)

    def create_new_project_version(self, project_name, project_template, version_name, description):
        """
        :param project_name: Project name
        :param project_template: Project template
        :param version_name: Version name
        :param description: Description of project version
        :return: A response object containing the newly created project and project version
        """
        issue_template = self.get_issue_template(project_template_id=project_template)
        issue_template_id = issue_template.data['data'][0]['_href']
        # SSC API returns the full url for the issue template, strip away just the ID
        issue_template_id = issue_template_id.rsplit('/', 1)[1]
        data = json.dumps(self.__formatted_new_application_version_payload__(project_name=project_name,
                                                                         version_name=version_name,
                                                                         issue_template_id=issue_template_id,
                                                                         description=description))
        url = '/ssc/api/v1/projectVersions'
        return self._request('POST', url, data=data)

    def download_artifact(self, artifact_id):
        """
        You might use this method like this, for example
            api = FortifyApi("https://my-fortify-server:my-port", token=get_token())
            response, file_name = api.download_artifact_scan("my-id")
            if response.success:
                file_content = response.data
                with open('/path/to/some/folder/' + file_name, 'wb') as f:
                    f.write(file_content)
            else:
                print response.message

        We've coded this for the entire file to load into memory. A future change may be to permit
        streaming/chunking of the file and handing back a stream instead of content.
        :param artifact_id: the id of the artifact to download
        :return: binary file data and file name
        """
        file_token = self.get_file_token('DOWNLOAD').data['data']['token']

        url = "/ssc/download/artifactDownload.html?mat=" + file_token + "&id=" + str(
            artifact_id) + "&clientVersion=" + self.client_version

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }

        response = self._request('GET', url, stream=True, headers=headers)

        try:
            file_name = response.headers['Content-Disposition'].split('=')[1].strip("\"'")
        except:
            file_name = ''

        return response, file_name

    def download_artifact_scan(self, artifact_id):
        """
        You might use this method like this, for example
            api = FortifyApi("https://my-fortify-server:my-port", token=get_token())
            response, file_name = api.download_artifact_scan("my-id")
            if response.success:
                file_content = response.data
                with open('/path/to/some/folder/' + file_name, 'wb') as f:
                    f.write(file_content)
            else:
                print response.message

        We've coded this for the entire file to load into memory. A future change may be to permit
        streaming/chunking of the file and handing back a stream instead of content.
        :param artifact_id: the id of the artifact scan to download
        :return: binary file data and file name
        """
        file_token = self.get_file_token('DOWNLOAD').data['data']['token']

        url = "/ssc/download/currentStateFprDownload.html?mat=" + file_token + "&id=" + str(
            artifact_id) + "&clientVersion=" + self.client_version + "&includeSource=true"

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }

        response = self._request('GET', url, stream=True, headers=headers)

        try:
            file_name = response.headers['Content-Disposition'].split('=')[1].strip("\"'")
        except:
            file_name = ''

        return response, file_name

    def get_artifact_scans(self, parent_id):
        """
        :param parent_id: parent resource identifier
        :return: A response object containing artifact scans
        """
        url = "/ssc/api/v1/artifacts/" + str(parent_id) + "/scans"
        return self._request('GET', url)

    def get_attribute_definition(self, search_expression):
        """
        :param search_expression: A fortify-formatted search expression, e.g. name:"Development Phase"
        :return: A response object containing the result of the get
        """
        if search_expression:
            try:
                # Python 2
                url = '/ssc/api/v1/attributeDefinitions?q=' + urllib.quote(str(search_expression))
            except:
                # Python 3
                url = '/ssc/api/v1/attributeDefinitions?q=' + urllib.parse.quote(str(search_expression))
            return self._request('GET', url)
        else:
            return FortifyResponse(message='A search expression must be provided', success=False)

    def get_attribute_definitions(self):
        """
        :return: A response object containing all attribute definitions
        """
        url = '/ssc/api/v1/attributeDefinitions?start=-1&limit=-1'
        return self._request('GET', url)

    def get_cloudscan_jobs(self):
        """
        :return: A response object containing all cloudscan jobs
        """
        url = '/ssc/api/v1/cloudjobs?start=-1&limit=-1'
        return self._request('GET', url)

    def get_cloudscan_job_status(self, scan_id):
        """
        :return: A response object containing a cloudscan job
        """
        url = '/ssc/api/v1/cloudjobs/' + scan_id
        return self._request('GET', url)

    def get_file_token(self, purpose):
        """
        :param purpose: specify if the token is for file 'UPLOAD' or 'DOWNLOAD'
        :return: a response body containing a file token for the specified purpose
        """

        url = "/ssc/api/v1/fileTokens"
        if purpose == 'UPLOAD':
            data = json.dumps(
                {
                    "fileTokenType": "UPLOAD"
                }
            )
        elif purpose == 'DOWNLOAD':
            data = json.dumps(
                {
                    "fileTokenType": "DOWNLOAD"
                }
            )
        else:
            return FortifyResponse(message='attribute purpose must be either UPLOAD or DOWNLOAD', success=False)

        return self._request('POST', url, data=data)

    def get_issue_template(self, project_template_id):
        """
        :param project_template_id: id of project template
        :return: A response object with data containing issue templates for the supplied project name
        """

        url = "/ssc/api/v1/issueTemplates" + "?limit=1&fields=q=id:\"" + project_template_id + "\""
        return self._request('GET', url)

    def get_project_version_artifacts(self, parent_id):
        """
        :param parent_id: parent resource identifier
        :return: A response object containing project version artifacts
        """
        url = "/ssc/api/v1/projectVersions/" + str(parent_id) + "/artifacts?start=-1&limit=-1"
        return self._request('GET', url)

    def get_project_version_attributes(self, project_version_id):
        """
        :param project_version_id: Project version id
        :return: A response object containing the project version attributes
        """
        url = '/ssc/api/v1/projectVersions/' + str(project_version_id) + '/attributes/?start=-1&limit=-1'
        return self._request('GET', url)

    def get_project_versions(self):
        """
        :return: A response object with data containing project versions
        """

        url = "/ssc/api/v1/projectVersions?start=-1&limit=-1"
        return self._request('GET', url)

    def get_projects(self):
        """
        :return: A response object with data containing projects
        """

        url = "/ssc/api/v1/projects?start=-1&limit=-1"
        return self._request('GET', url)

    def get_token(self, token_type=None, ttl=None):
        """
        :param token_type: token type to get
        :param ttl: ttl for the token
        :return: A response object with data containing create date, terminal date, and the actual token
        """

        url = '/ssc/api/v1/auth/token?'
        if token_type is not None:
            url = url + 'token=' + str(token_type) + '&'
        if ttl is not None:
            url = url + 'ttl=' + str(ttl)

        return self._request('GET', url)

    def post_attribute_definition(self, attribute_definition):
        """
        :param attribute_definition:
        :return:
        """
        url = '/ssc/api/v1/attributeDefinitions'
        data = json.dumps(attribute_definition)
        return self._request('POST', url, data=data)

    def upload_artifact_scan(self, file_path, project_version_id):
        """
        :param file_path: full path to the file to upload
        :param project_version_id: project_version_id
        :return: Response from the file upload operation
        """
        file_token = self.get_file_token('UPLOAD').data['data']['token']
        url = "/ssc/upload/resultFileUpload.html?mat=" + file_token
        files = {'file': (ntpath.basename(file_path), open(file_path, 'rb'))}

        headers = {
            'Accept': 'Accept:application/xml, text/xml, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }

        params = {
            'entityId': project_version_id,
            'clientVersion': self.client_version,
            'Upload': "Submit Query",
            'Filename': ntpath.basename(file_path)
        }

        response = self._request('POST', url, params, files=files, stream=True, headers=headers)

        return response

    def _request(self, method, url, params=None, files=None, data=None, headers=None, stream=False):
        """Common handler for all HTTP requests."""
        if not params:
            params = {}

        if not headers:
            headers = {
                'Accept': 'application/json'
            }
            if method == 'GET' or method == 'POST' or method == 'PUT':
                headers.update({'Content-Type': 'application/json'})
        headers.update({'User-Agent': self.user_agent})

        try:

            if self.auth_type == 'basic':
                response = requests.request(method=method, url=self.host + url, params=params, files=files,
                                            headers=headers, data=data,
                                            timeout=self.timeout, verify=self.verify_ssl,
                                            auth=(self.username, self.password), stream=stream)
            elif self.auth_type == 'token':
                response = requests.request(method=method, url=self.host + url, params=params, files=files,
                                            headers=headers, data=data,
                                            timeout=self.timeout, verify=self.verify_ssl,
                                            auth=FortifyTokenAuth(self.token), stream=stream)
            else:
                response = requests.request(method=method, url=self.host + url, params=params, files=files,
                                            headers=headers, data=data,
                                            timeout=self.timeout, verify=self.verify_ssl, stream=stream)

            try:
                response.raise_for_status()

                # two flavors of response are successful, GETs return 200, PUTs return 204 with empty response text
                response_code = response.status_code
                success = True if response_code // 100 == 2 else False
                if response.text:
                    try:
                        data = response.json()
                    except ValueError:  # Sometimes the returned data isn't JSON, so return raw
                        data = response.content

                return FortifyResponse(success=success, response_code=response_code, data=data,
                                       headers=response.headers)
            except ValueError as e:
                return FortifyResponse(success=False, message="JSON response could not be decoded {0}.".format(e))
        except requests.exceptions.SSLError as e:
            return FortifyResponse(message='An SSL error occurred. {0}'.format(e.message), success=False)
        except requests.exceptions.ConnectionError as e:
            return FortifyResponse(message='A connection error occurred. {0}'.format(e.message), success=False)
        except requests.exceptions.Timeout:
            return FortifyResponse(message='The request timed out after ' + str(self.timeout) + ' seconds.',
                                   success=False)
        except requests.exceptions.RequestException as e:
            return FortifyResponse(
                message='There was an error while handling the request. {0}'.format(e.message), success=False)


class FortifyTokenAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = 'FortifyToken ' + self.token
        return r


class FortifyResponse(object):
    """Container for all Fortify SSC API responses, even errors."""

    def __init__(self, success, message='OK', response_code=-1, data=None, headers=None):
        self.message = message
        self.success = success
        self.response_code = response_code
        self.data = data
        self.headers = headers

    def __str__(self):
        if self.data:
            return str(self.data)
        else:
            return self.message

    def data_json(self, pretty=False):
        """Returns the data as a valid JSON string."""
        if pretty:
            return json.dumps(self.data, sort_keys=True, indent=4, separators=(',', ': '))
        else:
            return json.dumps(self.data)
