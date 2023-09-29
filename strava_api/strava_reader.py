import datetime
import json
import pandas as pd
from strava_client import StravaClient
import os
import time


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
        n_calls = n_page
        refined_act = list()
        for this_act in activity_list:
            if n_calls < 200:
                # Strava limits calls to 200 per 15minutes
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
                n_calls += 1
            else:
                print("Reached API limits, try again in 15minutes")
                n_calls = 1
                time.sleep(900)

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


if __name__ == "__main__":
    # All of this is hard codded right now...
    with open('./config_strava.json', 'r') as f:
        config_dict = json.load(f)

    strava_reader = StravaReader(config_dict)
    # Load data and store it as an excel for simplicity
    if os.path.isfile('../data/strava.xlsx'):
        df = pd.read_excel('../data/strava.xlsx')
        os.rename('../data/strava.xlsx', '../data/strava_old.xlsx')
        df = strava_reader.update_data(df)
        df['date'] = df['date'].dt.tz_localize(None)
        df.to_excel('../data/strava.xlsx')
    else:
        df = strava_reader.initialize_data(after=datetime.datetime(2023, 5, 1))
        df['date'] = df['date'].dt.tz_localize(None)
        df.to_excel('../data/strava.xlsx')
