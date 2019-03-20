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


def parseID(id):
    numbers = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"] 
    id = "".join(id.split())
    id = id.replace("-", "")
    id = id.replace("_", "")
    id_array = re.findall('\d+|\D+', id)
    proper_array = []
    for i in id_array:
         proper_array.append(sortID(i))
    print(proper_array)
    new_id = "".join(proper_array)
    return new_id

def sortID(string):
    numbers = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    for num in numbers:
        if string == num:
            return str(numbers.index(num))
    return string

class TimetableSkill(MycroftSkill):

    def __init__(self):
        logger.info('init is working')
        super(TimetableSkill, self).__init__(name="TimetableSkill")
        self.timetable = self._lookup(self.settings.get("student_id"))

    @intent_handler(IntentBuilder("").require("How_many").require("day"))
    def handle_how_many(self, message):
        day = message.data.get("day")
        if day == "today":
            
            current_day = datetime.date.today()
            current_weekday = calendar.day_name[current_day.weekday()].lower()
            index_day = self.assertDay(current_weekday)
            count = 0
            if self.timetable.days[index_day] is None:
                self.speak_dialog("You have no classes listed for that day")
                return
            for lesson in self.timetable.days[index_day]:
                count = count + 1
            if count == 0:
                self.speak_dialog("no_lessons")
                return
            fir = self.timetable.days[index_day][0]
            self.speak_dialog("number_lessons", {"num": count, "day":day})
            self.speak_dialog("fir_count", {"time": fir.startTime, "day": day,
                "module":fir.module, "place":fir.location})
            return
        if day == "tomorrow":
            
            current_day = datetime.date.today()
            current_weekday = calendar.day_name[current_day.weekday()].lower()
            index_day = self.assertDay(current_weekday) + 1
            count = 0
            if self.timetable.days[index_day] is None:
                self.speak_dialog("You have no classes listed for that day")
                return
            for lesson in self.timetable.days[index_day]:
                count = count + 1
            if count == 0:
                self.speak_dialog("no_lessons")
                return
            fir = self.timetable.days[index_day][0]
            self.speak_dialog("number_lessons", {"num": count, "day":day})
            self.speak_dialog("fir_count", {"time": fir.startTime, "day": day,
                "module":fir.module, "place":fir.location})
            return

        index = self.assertDay(day)
        print(index)
        count = 0
        for lesson in self.timetable.days[index]:
            count = count + 1
        if count == 0:
            self.speak_dialog("no_lessons")
            return
        fir = self.timetable.days[index][0]
        self.speak_dialog("number_lessons", {"num": count, "day":day.capitalize()})
        self.speak_dialog("fir_count", {"time": fir.startTime, "day": day.capitalize(),
            "module":fir.module, "place":fir.location})

    @intent_handler(IntentBuilder("").require("More")
                    .require("module"))
    def handle_tell_more(self, message):
        module_id = message.data.get("module")
        module_id = parseID(module_id)
        self._handle_module_detail_request(module_id)

    @intent_handler(IntentBuilder("").require("Mod_query").require("Type")
                    .require("module_id"))
    def handle_module_details(self, message):
        module_id = message.data.get("module_id")
        module_id = parseID(module_id)
        self._handle_module_detail_request(module_id)

    @intent_handler(IntentBuilder("").require("General_Query").require("lesson").require("do")
                    .require("pos").require("day"))
    def handle_class_day(self, message):
        pos = message.data.get("pos").split()[0]
        if pos == "on":
            pos = "last"
        self._handle_query(pos, message.data.get("day"))

    @intent_handler(IntentBuilder("").require("General_Query")
                    .require("Pronoun").require("Next").require("Type"))
    def handle_next_lesson(self, message):
        self._handle_next_lesson()

    @intent_handler(IntentBuilder("").require("next_type").require("type_lesson").require("for")
                    .require("module_type"))
    def handle_next_type(self, message):
        print("hello brian its working you legend")
        print(message.data.get("type_lesson"))
        print(message.data.get("module_type"))
        self._handle_next_type(message.data.get("type_lesson"),
                                parseID(message.data.get("module_type")))

    @intent_handler(IntentBuilder("").require("General_Query")
                    .require("Starting").require("Type").require("day"))
    def handle_first_lesson_req(self, message):
        day = message.data.get("day")
        self._handle_first_les(day)

    @intent_handler(IntentBuilder("").require("General_Query")
                    .require("Pronoun").require("type_lesson"))
    def handle_type_lesson(self, message):
        print("hello world")
        self._handle_only_next_type(message.data.get("type_lesson"))

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
        self._handle_next_lesson_location()

    @intent_handler(IntentBuilder("").require("next_lesson_for_module").require("module_id"))
    def request_next_lesson_for_module(self, message):
        days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday",
                        "saturday"]
        m_id = message.data.get("module_id")
        m_id = parseID(m_id)
        current_day = datetime.date.today()
        current_weekday = calendar.day_name[current_day.weekday()].lower()
        index_day = self.assertDay(current_weekday)
        day_in, lesson = self._handle_find_module(index_day, m_id)
        if lesson == None:
            self.speak_dialog("Could not find module i.d, possibly not valid")
            return
        lesson.slot_type = self._parse_slot_type(lesson.slot_type)
        if day_in == index_day:
            self.speak_dialog("next_module_time", {"module":m_id, "type": lesson.slot_type,
                "day":"today", "time": lesson.startTime, "place": lesson.location})
        elif day_in+1 == index_day:
            self.speak_dialog("next_module_time", {"module":m_id, "type": lesson.slot_type,
                "day":"tomorrow", "time": lesson.startTime, "place": lesson.location})
        else:
            self.speak_dialog("next_module_time", {"module":m_id, "type": lesson.slot_type,
                "day":days_of_week[day_in], "time": lesson.startTime, "place": lesson.location})


    @intent_handler(IntentBuilder("").require("Q_lecture_tomorrow"))
    def Question_lectures_tomorrow(self, message):
        self._handle_q_query("first", calendar.day_name[datetime.datetime
                                                        .today().weekday()+1])

    @intent_handler(IntentBuilder("").require("General_Query")
                    .require("Pronoun").require("pos").require("Type")
                    .require("today"))
    def handle_class_today(self, message):
        print("HEY")
        pos = message.data.get("pos")
        if pos == "on" or pos == "is":
            pos = "last"
        self._handle_query(pos, calendar.day_name[datetime.datetime
                                                  .today().weekday()])

    @intent_handler(IntentBuilder("").require("Request").require("id"))
    def handle_intent(self, message):
        id = parseID(message.data.get("id"))
        print(id)
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
        if module_details.name is None:
            self.speak_dialog("no_entry_found")
            return

        if module_details.lecturer is None:
            self.speak_dialog("no_entry_found")
            return

        self.speak_dialog("module_details_ans",
                          {"id": module_id, "name": module_details.name,
                           "lecturer": module_details.lecturer})

    def _handle_find_module(self, index_day, module):
        i = 0
        for day in self.timetable.days[index_day:]:
            if not day:
                continue
            for lesson in day:
                if lesson.module.lower() == module:
                    return index_day+i, lesson
            i = i + 1
        return None, None

    def _parse_slot_type(self, slot_type):
        if slot_type.split("-")[0] == "TUT":
            return "Tutorial"
        if slot_type.split("-")[0] == "LEC":
            return "Lecture"
        if slot_type.split("-")[0] == "LAB":
            return "Lab"
        return slot_type

    def _lookup(self, student_id):
        try:
            timetable = webscrape.simple_get(student_id)
            if not timetable:
                self.speak_dialog("no entry found")
                return
        except Exception:
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

    def _handle_next_type(self, l_type, module):
        days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday",
                        "saturday"]
        counter = 0
        for day in self.timetable.days:
            if not day:
                counter = counter + 1
                continue
            for lesson in day:
                print(lesson.slot_type)
                lesson.slot_type = self._parse_slot_type(lesson.slot_type)
                print(l_type, lesson.slot_type)
                if l_type == lesson.slot_type.lower():
                    print(module, lesson.module)
                    if module == lesson.module.lower():
                        print(days_of_week[counter])
                        print("we made it")
                        self.speak_dialog("_next_type", {"type": l_type, "module":lesson.module,
                                            "day": days_of_week[counter], "time": lesson.startTime,
                                            "room": lesson.location})
                        return
            counter = counter + 1
        self.speak_dialog("cant_find_type", {"type": l_type, "module_id": module})

    def _handle_only_next_type(self, l_type):
        days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday",
                        "saturday"]
        counter = 0
        print("doing this")
        for day in self.timetable.days:
            if not day:
                counter = counter + 1
                continue
            for lesson in day:
                print(lesson.slot_type)
                lesson.slot_type = self._parse_slot_type(lesson.slot_type)
                print(l_type, lesson.slot_type.lower())
                if l_type == lesson.slot_type.lower():
                    self.speak_dialog("_next_type", {"type": l_type, "module":lesson.module,
                                    "day": days_of_week[counter], "time": lesson.startTime,
                                    "room": lesson.location})
                    return
        counter = counter + 1
        self.speak_dialog("cant_find_type", {"type": l_type, "module_id": lesson.module})

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
        day[lecture_index].slot_type = self._parse_slot_type(day[lecture_index].slot_type)
        print(day[lecture_index].slot_type)
        self.speak_dialog("lecture_q_info",
                           {"type": day[lecture_index].slot_type,
                           "module": day[lecture_index].module,
                           "s_time": day[lecture_index].startTime,
                           "location": day[lecture_index].location})

        self.set_context("module", day[lecture_index].module)

    def _handle_query(self, position, day):
        print(day.lower())
        week_index = self.assertDay(day.lower())
        print(week_index)
        if week_index is None:
            print("brian")
            return None
        lecture_index = self.assertPosition(position)

        print(lecture_index, "index")
        day = self.timetable.days[week_index]

        if not day:
            self.speak_dialog("no_lessons")
            return None

        if lecture_index == last_position:
            lecture_index = len(day)-1

        if len(day) < (lecture_index+1):
            self.speak_dialog("no_lecture")
            return None

        day[lecture_index].slot_type = self._parse_slot_type(day[lecture_index].slot_type)
        print(day[lecture_index].slot_type)
        self.speak_dialog("lecture_info", {"type": day[lecture_index].slot_type,
                          "module": day[lecture_index].module,
                          "s_time": day[lecture_index].startTime,
                          "location": day[lecture_index].location})

        self.set_context("module", day[lecture_index].module)

    def _handle_first_les(self, req_day):
        week_index = self.assertDay(req_day)
        day = self.timetable.days[week_index]

        day[INITIAL_LESSON].slot_type = self._parse_slot_type(day[INITIAL_LESSON].slot_type)
        self.speak_dialog("first_lec_ans",
                           {"type": day[INITIAL_LESSON].slot_type,
                           "day": req_day,
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

        days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday",
                        "saturday"]
        if not next_lesson:
            self.speak_dialog("no_more_lessons")
            current_day = datetime.date.today()
            current_weekday = calendar.day_name[current_day.weekday()].lower()

            week_index = self.assertDay(current_weekday)
            c = week_index +1
            while(1):
                day = self.timetable.days[c]
                if day is None:
                    if c == 5:
                        c = 0;
                    else:
                        c = c + 1
                else:
                    day[0].startTime = datetime.datetime.strptime(day[0].startTime,
                                                  "%H:%M")
                    day[0].startTime = datetime.datetime.strftime(day[0].startTime,
                                                  "%I:%M %p")
                    self.speak_dialog("nl", {"day": days_of_week[c], "module": day[0].module,
                                    "time": day[0].startTime, "place": day[0].location})
                    self.set_context("module", day[0].module)
                    return
            return

        self.speak_dialog("next_lesson_location",
                          {"location": next_lesson.location})

    def _handle_next_lesson(self):
        nl = self._get_next_lesson()  # next lesson

        days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday",
                        "saturday"]
        if not nl:
            self.speak_dialog("no_more_lessons")
            current_day = datetime.date.today()
            current_weekday = calendar.day_name[current_day.weekday()].lower()

            week_index = self.assertDay(current_weekday)
            c = week_index +1
            while(1):
                day = self.timetable.days[c]
                if day is None:
                    if c == 5:
                        c = 0;
                    else:
                        c = c + 1
                else:
                    self.speak_dialog("nl", {"day": days_of_week[c], "module": day[0].module,
                                    "time": day[0].startTime, "place": day[0].location})
                    self.set_context("module", day[0].module)
                    return
            return
        nl.startTime = datetime.datetime.strptime(nl.startTime,
                                                  "%H:%M")
        nl.startTime = datetime.datetime.strftime(nl.startTime,
                                                  "%I:%M %p")
        self.speak_dialog("next_lesson", {"module": nl.module,
                                          "startTime": nl.startTime})
        self.set_context("module", nl.module)

    def _subtract_times(self, time1, time2):
        time1 = time1.split(" ", 1)[0]
        timeA = datetime.datetime.strptime(time1, "%H:%M")
        timeB = datetime.datetime.strptime(time2, "%H:%M")
        newTime = timeA - timeB

        if (newTime.seconds/60 > LECTURE_TIME_LIMIT):
            return None

        return newTime.seconds/60


def create_skill():
    return TimetableSkill()
