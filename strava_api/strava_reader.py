import datetime
import json
import pandas as pd
from strava_client import StravaClient

class StravaReader:
    def __init__(self, strava_api_config):
        # Create a client with a working access token
        self.client = StravaClient(strava_api_config).post_refresh_token()

    def initialize_data(self, after, per_page=30):
        """
        Initialize the dataframe of all activities after a given date
        :param after: First day for the data collection (timestamp or datetime)
        :param per_page: number of activities per page for the list request
        :return:
        """
        continue_cond = True
        activity_list = list()
        n_page = 1
        if isinstance(after, datetime.datetime):
            after = int(after.timestamp())
        elif isinstance(after, int):
            pass
        else:
            raise TypeError("after must be datetime.datetime or int")
        while continue_cond:
            part_list = self.client.get_activity_list(per_page=per_page, page=n_page, after=after)
            activity_list.extend(part_list)
            if ((len(part_list) == per_page)
                    and (pd.to_datetime(part_list[-1]["start_date"]).timestamp() > after)
                    and (n_page < 100)):
                continue_cond = True
                n_page += 1
            else:
                continue_cond = False

        refined_act = list()
        for this_act in activity_list:
            act_id = this_act['id']
            act_dict = self.client.get_activity(act_id)
            refined_act.append({'name': act_dict["name"],
                                'description': act_dict['description'],
                                'distance': act_dict["distance"],
                                'sport_type': act_dict["sport_type"],
                                'date': pd.to_datetime(act_dict['start_date']),
                                'rpe': act_dict["perceived_exertion"],
                                'time': act_dict["moving_time"],
                                'type': act_dict["type"],
                                'workout_type': act_dict.get('workout_type'),
                                "average_speed": act_dict['average_speed'],
                                "max_speed": act_dict['max_speed'],
                                })

        df_act = pd.DataFrame(refined_act)
        return df_act

    def update_data(self, df, per_page=30):
        """
        Update the dataframe of all activities
        :param df: dataframe to update
        :param per_page: number of pages for the list request
        :return: updated dataframe
        """
        sorted_df = df.sort_values(by='date', ascending=False)
        last_date = df.date.max()
        new_df = self.initialize_data(after=last_date, per_page=per_page)

        return pd.concat([sorted_df, new_df], axis=1)
