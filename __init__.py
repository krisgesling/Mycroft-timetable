import re
import calendar
import datetime

from .Webscraping import webscrape
from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.util.log import getLogger
from mycroft.util.parse import extract_datetime

logger = getLogger(__name__)

LECTURE_TIME_LIMIT = 540
last_position = 7
INITIAL_LESSON = 0


class TimetableSkill(MycroftSkill):

    def __init__(self):
        logger.info('init is working')
        super(TimetableSkill, self).__init__(name="TimetableSkill")
        self.timetable = self._lookup(self.settings.get("student_id"))

    @intent_handler(IntentBuilder("").require("More")
                    .require("module"))
    def handle_tell_more(self, message):
        module_id = message.data.get("module")
        self._handle_module_detail_request(module_id)

    @intent_handler(IntentBuilder("").require("Mod_query").require("Type")
                    .require("module_id"))
    def handle_module_details(self, message):
        module_id = message.data.get("module_id")
        self._handle_module_detail_request(module_id)

    @intent_handler(IntentBuilder("").require("General_Query")
                    .require("Pronoun").require("Next").require("Type"))
    def handle_next_lesson(self, message):
        self._handle_next_lesson()

    @intent_handler(IntentBuilder("").require("General_Query")
                    .require("Starting").require("Type").require("day"))
    def handle_first_lesson_req(self, message):
        day = message.data.get("day")
        self._handle_first_les(day)

    @intent_handler(IntentBuilder("").require("General_Query")
                    .require("Pronoun").require("pos").require("Type")
                    .require("day"))
    def handle_query_class(self, message):
        pos = message.data.get("pos")
        if pos == "on":
            pos = "last"
        day = message.data.get("day")
        self._handle_query(pos, day)

    @intent_handler(IntentBuilder("").require("General_Query")
                    .require("Pronoun").require("pos").require("Type")
                    .require("tomorrow"))
    def handle_class_tomorrow(self, message):
        pos = message.data.get("pos")
        if pos == "on" or pos == "is":
            pos = "last"
        day = datetime.datetime.today().weekday()+1
        if day is 7:
            day = 0
        self._handle_query(pos, calendar.day_name[day])

    @intent_handler(IntentBuilder("").require("Q_lecture"))
    def Question_lectures(self, message):
        self._handle_q_query("first", calendar.day_name[datetime.datetime
                                                        .today().weekday()])

    @intent_handler(IntentBuilder("").require("next_lesson_loc"))
    def next_lesson_loc(self, message):
        print("hello lesson")
        self._handle_next_lesson_location()

    @intent_handler(IntentBuilder("").require("Q_lecture_tomorrow"))
    def Question_lectures_tomorrow(self, message):
        self._handle_q_query("first", calendar.day_name[datetime.datetime
                                                        .today().weekday()+1])

    @intent_handler(IntentBuilder("").require("General_Query")
                    .require("Pronoun").require("pos").require("Type")
                    .require("today"))
    def handle_class_today(self, message):
        pos = message.data.get("pos")
        if pos == "on" or pos == "is":
            pos = "last"
        self._handle_query(pos, calendar.day_name[datetime.datetime
                                                  .today().weekday()])

    @intent_handler(IntentBuilder("").require("Request").require("id"))
    def handle_intent(self, message):
        id = message.data.get("id")
        self.speak_dialog("searching", {"query": id})
        tt = self._lookup(id)
        if not tt:
            self.speak_dialog("invalid_id")
        else:
            self.settings["student_id"] = id
            self.speak_dialog("successful_change")
            self.timetable = tt

    def _handle_module_detail_request(self, module_id):
        module_details = webscrape.get_module_details(module_id)
        if not module_details:
            self.speak_dialog("no entry found")
            return
        self.speak_dialog("module_details_ans",
                          {"id": module_id, "name": module_details.name,
                           "lecturer": module_details.lecturer})

    def _lookup(self, student_id):
        try:
            timetable = webscrape.simple_get(student_id)
            if not timetable:
                self.speak_dialog("no entry found")
                return
        except:
            self.speak_dialog("no entry found")
        return timetable

    def assertDay(self, chosen_day):
        chosen_day = chosen_day.lower()
        days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday",
                        "saturday"]
        for day in days_of_week:
            if chosen_day == day:
                return days_of_week.index(day)
        self.speak_dialog("invalid_argument")
        return None

    def assertPosition(self, chosen_pos):
        valid_position = ["first", "second", "third", "fourth", "fifth",
                          "sixth", "seventh", "last"]
        for position in valid_position:
            if chosen_pos == position:
                return valid_position.index(position)
        self.speak_dialog("invalid_argument")
        return None

    def _handle_q_query(self, position, day):
        week_index = self.assertDay(day)
        lecture_index = self.assertPosition(position)

        day = self.timetable.days[week_index]

        if not day:
            self.speak_dialog("no_lessons")
            return None

        if lecture_index == last_position:
            lecture_index = len(day)-1

        if len(day) < (lecture_index+1):
            self.speak_dialog("no_lecture")
            return None

        self.speak_dialog("lecture_q_info",
                          {"module": day[lecture_index].module,
                           "s_time": day[lecture_index].startTime,
                           "location": day[lecture_index].location})

        self.set_context("module", day[lecture_index].module)

    def _handle_query(self, position, day):
        week_index = self.assertDay(day)
        lecture_index = self.assertPosition(position)

        day = self.timetable.days[week_index]

        if not day:
            self.speak_dialog("no_lessons")
            return None

        if lecture_index == last_position:
            lecture_index = len(day)-1

        if len(day) < (lecture_index+1):
            self.speak_dialog("no_lecture")
            return None

        self.speak_dialog("lecture_info", {"module": day[lecture_index].module,
                          "s_time": day[lecture_index].startTime,
                          "location": day[lecture_index].location})

        self.set_context("module", day[lecture_index].module)

    def _handle_first_les(self, req_day):
        week_index = self.assertDay(req_day)
        day = self.timetable.days[week_index]

        self.speak_dialog("first_lec_ans",
                          {"day": req_day,
                           "time": day[INITIAL_LESSON].startTime})

    def _get_current_time(self):
        now = datetime.datetime.now()
        cur_time = str(now)
        cur = cur_time.split(":")
        cur_time = cur[0] + ":" + cur[1]
        cur_time = cur_time.split(" ")
        cur_time = cur_time[1]
        current_time = datetime.datetime.strptime(cur_time, "%H:%M")
        current_time = current_time.strftime("%H:%M")
        return current_time

    def _get_next_lesson(self):
        current_day = datetime.date.today()
        current_weekday = calendar.day_name[current_day.weekday()].lower()

        week_index = self.assertDay(current_weekday)

        day = self.timetable.days[week_index]
        current_time = self._get_current_time()
        next_lesson = None
        time_dif = None

        if day is None:
            return

        for lesson in day:
            time_dif = self._subtract_times(lesson.startTime, current_time)
            if time_dif:
                return lesson

        return None

    def _handle_next_lesson_location(self):
        next_lesson = self._get_next_lesson()

        if not next_lesson:
            self.speak_dialog("no_more_lessons")
            return

        self.speak_dialog("next_lesson_location",
                          {"location": next_lesson.location})

    def _handle_next_lesson(self):
        next_lesson = self._get_next_lesson()

        if not next_lesson:
            self.speak_dialog("no_more_lessons")
            return
        next_lesson.startTime = datetime.datetime.
        strptime(next_lesson.startTime, "%H:%M")
        next_lesson.startTime = datetime.datetime.
        strftime(next_lesson.startTime, "%I:%M %p")
        self.speak_dialog("next_lesson", {"module": next_lesson.module,
                                          "startTime": next_lesson.startTime})
        self.set_context("module", next_lesson.module)

    def _subtract_times(self, time1, time2):
        timeA = datetime.datetime.strptime(time1, "%H:%M")
        timeB = datetime.datetime.strptime(time2, "%H:%M")
        newTime = timeA - timeB

        if (newTime.seconds/60 > LECTURE_TIME_LIMIT):
            return None

        return newTime.seconds/60


def create_skill():
    return TimetableSkill()
