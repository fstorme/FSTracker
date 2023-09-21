import datetime
import json
import pandas as pd
from strava_client import StravaClient

class StravaReader:
    def __init__(self, strava_api_config):
        # Create a client with a working access token
        self.client = StravaClient(strava_api_config).post_refresh_token()

    def initialize_data(self, after, per_page=30):
        continue_cond = True
        activity_list = list()
        n_page = 1
        while continue_cond:
            part_list = self.client.get_activity_list(per_page=per_page, page=n_page, after=after)
            activity_list.extend(part_list)
            if (len(part_list) == per_page) and (part_list[-1]["start_date"] > after) and (n_page < 100):
                continue_cond = True
                n_page += 1
            else:
                continue_cond = False

        refined_act = list()
        for this_act in activity_list:
            act_id = this_act['id']
            act_dict = self.client.get_activity(act_id)
            refined_act.append({'name': act_dict["name"],
                                'comments': act_dict['description'],
                                'distance': act_dict["distance"],
                                'sport_type': act_dict["sport_type"],
                                'date': act_dict['start_date'],
                                'rpe': act_dict["perceived_exertion"],
                                'time': act_dict["moving_time"],
                                'type': act_dict["type"],
                                'workout_type': act_dict.get('workout_type'),
                                "average_speed": act_dict['average_speed'],
                                "max_speed": act_dict['max_speed'],
                                })

        df_act = pd.DataFrame(refined_act)
        return df_act

