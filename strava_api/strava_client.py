import requests
import requests.auth
import time
import datetime


class BearerAuth(requests.auth.AuthBase):
    """
    Class for bearer token authorization
    """
    def __init__(self, token):
        """
        instantiate an instance of bearer authorization
        :param token: access_token from strava
        """
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r

class StravaClient:
    """
    Basic strava client for activity analysis
    """
    def __init__(self, config_dict):
        self.refresh_token = config_dict['refresh_token']
        self.client_id = config_dict['client_id']
        self.client_secret = config_dict['client_secret']
        self.expires_at = 0
        self.access_token = None

    def post_refresh_token(self):
        """
        Update the access token based on the client configuration
        :return: updated client
        """
        if self.access_token and (time.time()<self.expires_at):
            return self

        param_call = {'client_id': self.client_id,
                      'client_secret': self.client_secret,
                      'grant_type': "refresh_token",
                      'refresh_token': self.refresh_token
                      }

        r = requests.post("https://www.strava.com/oauth/token", params=param_call)
        if r.status_code == 200:
            out_dir = r.json()
            self.access_token = out_dir['access_token']
            self.expires_at = out_dir['expires_at']
            self.refresh_token = out_dir['refresh_token']
        else:
            raise Exception("Refresh token post exception, status {}".format(r.status_code))

        return self

    def get_logged_athlete(self):
        """
        Get logged athlete profile
        :return: dict with the athlete profile
        """
        if self.access_token is None:
            raise Exception('Access Token not initialized')

        auth = BearerAuth(self.access_token)
        r = requests.get("https://www.strava.com/api/v3/athlete", auth=auth)
        if r.status_code == 200:
            return r.json()
        else:
            raise Exception("Get logged athlete exception, status {}".format(r.status_code))

    def get_activity_list(self, per_page=30, page=1, before=None, after=None):
        """
        Get the list of activities for the logged athlete
        :param per_page: number of activities per pages
        :param page: page to access
        :param before: int or datetime, access activities before this date
        :param after: int or datetime, access activities after this date
        :return: list of dict of the summary of activities
        """
        if self.access_token is None:
            raise Exception('Access Token not initialized')

        endpoint = "https://www.strava.com/api/v3/athlete/activities"
        auth = BearerAuth(self.access_token)
        params_call = dict()
        if isinstance(per_page, int):
            params_call["per_page"] = per_page
        else:
            raise TypeError("per_page must be int")

        if isinstance(page, int):
            params_call["page"] = page
        else:
            raise TypeError("page must be int")

        if before is not None:
            if isinstance(before, datetime.datetime):
                params_call['before'] = int(before.timestamp())
            elif isinstance(before, int):
                params_call['before'] = before
            else:
                raise TypeError("before must be int or datetime")

        if after is not None:
            if isinstance(after, datetime.datetime):
                params_call['after'] = int(after.timestamp())
            elif isinstance(after, int):
                params_call['after'] = after
            else:
                raise TypeError("after must be int or datetime")

        r = requests.get(endpoint, params=params_call, auth=auth)
        if r.status_code == 200:
            return r.json()
        else:
            raise Exception("Get list activities logged athlete exception, status {}".format(r.status_code))

    def get_activity(self, act_id):
        """
        Get details on an activity
        :param act_id: id of the activity to access
        :return: dict for this activity
        """
        if not isinstance(act_id, int):
            raise TypeError("act_id must be int")
        if self.access_token is None:
            raise Exception('Access Token not initialized')

        auth = BearerAuth(self.access_token)
        endpoint = "https://www.strava.com/api/v3/activities/{}".format(act_id)
        r = requests.get(endpoint, auth=auth)
        if r.status_code == 200:
            return r.json()
        else:
            raise Exception("Get activity exception, status {}".format(r.status_code))
