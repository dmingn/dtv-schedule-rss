import datetime

from app.channel import Program


def test_program_rss_description():
    program = Program(
        title="Sample Program",
        url=None,
        description="This is a test description.",
        start=datetime.datetime(2025, 3, 20, 15, 30, tzinfo=datetime.timezone.utc),
    )

    expected_description = "03/20 15:30\n\nThis is a test description."

    assert program.rss_description == expected_description


def test_program_rss_description_without_description():
    program = Program(
        title="Sample Program",
        url=None,
        description=None,
        start=datetime.datetime(2025, 3, 20, 15, 30, tzinfo=datetime.timezone.utc),
    )

    expected_description = "03/20 15:30"

    assert program.rss_description == expected_description


def test_program_rss_pub_date():
    start_date = datetime.datetime(2025, 3, 20, 15, 30, tzinfo=datetime.timezone.utc)

    program = Program(
        title="Sample Program",
        url=None,
        description="This is a test description.",
        start=start_date,
    )

    expected_pub_date = start_date - datetime.timedelta(days=7)

    assert program.rss_pub_date == expected_pub_date
