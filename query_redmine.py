import datetime
from redminelib import Redmine
from redminelib.exceptions import ResourceAttrError
from plotly.offline import plot
import plotly.graph_objs as go

dt_format = '%Y-%m-%d'
team = 'y'

def get_current_sprint_info():
    sprint0_end = datetime.datetime(2017, 9, 26, 0, 0, 0, 0)
    today = datetime.datetime.today()

    due_date = sprint0_end
    sprint_count = 0
    while due_date < today:
            sprint_count += 1
            start_date = due_date + datetime.timedelta(days=1)
            due_date += datetime.timedelta(days=14)
    return {'num': sprint_count, 'start_date': start_date, 'due_date': due_date}


def get_sprint_date_interval(sprint_info):
    return [(sprint_info['start_date'] + datetime.timedelta(days=x)).strftime(dt_format) for x in range(0, 14)]


def plot_chart(sprint_info, total_story_points, actual_remaining):
    team_name = "YaST" if team == "y" else "User space"
    date_list = get_sprint_date_interval(sprint_info)

    trace_ideal_burn = go.Scatter(
        x=date_list,
        y=[x / 13.0 for x in range(13*total_story_points, -1, -total_story_points)],
        name="Ideal stories remaining",
        textsrc="gohals:114:c99b6e",
        type="scatter",
        uid="2b2777",
        xsrc="gohals:114:5be4af",
        ysrc="gohals:114:c99b6e"
    )
    trace_current_burn = go.Scatter(
        x=date_list,
        y=list(actual_remaining.values()),
        name="Actual stories remaining",
        textsrc="gohals:114:c99b6e",
        type="scatter",
        uid="a7c235",
        xsrc="gohals:114:5be4af",
        ysrc="gohals:114:d49a4c"
    )
    data = go.Data([trace_ideal_burn, trace_current_burn])
    layout = go.Layout(
        autosize=True,
        height=600,
        width=1000,
        title="Sprint " + str(sprint_info['num']) + " - Burndown chart - " + team_name + " QSF team",
        xaxis=dict(
            title="Iteration Timeline (working days)",
            autorange=True,
            range=date_list,
            type="date",
            tickvals=date_list
        ),
        yaxis=dict(
            title="Sum of Story Estimates (story points)",
            autorange=True,
            range=[-1, 25],
            type="linear"
        )
    )

    fig = go.Figure(data=data, layout=layout)
    plot(fig)


def init_actual_remaining(sprint_info):
    actual_remaining = dict.fromkeys(get_sprint_date_interval(sprint_info))
    for str_date in actual_remaining:
        date = datetime.datetime.strptime(str_date, dt_format)
        if date <= datetime.datetime.today():
            actual_remaining[str_date] = 0
    return actual_remaining


def query_redmine(sprint_info):
    project_list = ['suseqa', 'openqav3', 'openqatests']
    str_start_date = sprint_info['start_date'].strftime(dt_format)
    str_due_date = sprint_info['due_date'].strftime(dt_format)
    date_interval = '><' + str_start_date + '|' + str_due_date
    rm = Redmine('https://progress.opensuse.org', key='dc97b2582634ac80ee3a1cc388c324d6ff413a44')
    return rm.issue.filter(project_ids=project_list, status_id='*', due_date=date_interval, subject="~[" + team + "]")


def adjust_remaining(actual_remaining, total_story_points):
    remaining_story_points = total_story_points
    for str_date in actual_remaining:
        if actual_remaining[str_date]:
            remaining_story_points += actual_remaining[str_date]
            actual_remaining[str_date] = remaining_story_points
    return actual_remaining


def calculate_burn():
    total_story_points = 0
    actual_remaining = init_actual_remaining(sprint_info)
    for num, story in enumerate(stories, start=1):
        try:
            story_points = int(story.estimated_hours)
        except ResourceAttrError:
            story_points = 0
        total_story_points += story_points

        if story.status.name == "Resolved":
            closed_on = story.closed_on
            dt = datetime.datetime(closed_on.year, closed_on.month, closed_on.day, 0, 0, 0, 0).strftime(dt_format)
            actual_remaining[dt] -= story_points

        print("[{0:2}] {1} -> {2}".format(num, story.subject, story_points))
    actual_remaining = adjust_remaining(actual_remaining, total_story_points)
    return actual_remaining, total_story_points


def create_burndown_chart(actual_remaining, total_story_points):
    str_today_date = datetime.datetime.today().strftime(dt_format)
    str_yesterday_date = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime(dt_format)
    if actual_remaining[str_today_date] == 0:
        if sprint_info['start_date'] == datetime.datetime.today():
            actual_remaining[str_today_date] = total_story_points
        else:
            actual_remaining[str_today_date] = actual_remaining[str_yesterday_date]

    plot_chart(sprint_info, total_story_points, actual_remaining)


sprint_info = get_current_sprint_info()
stories = query_redmine(sprint_info)
actual_remaining, total_story_points = calculate_burn()
create_burndown_chart(actual_remaining, total_story_points)