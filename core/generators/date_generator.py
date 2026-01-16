class DateGenerator:
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date

    def __iter__(self):
        self.current_date = self.start_date
        return self

    def __next__(self):
        if self.current_date > self.end_date:
            raise StopIteration
        else:
            date_str = self.current_date.strftime("%Y-%m-%d")
            self.current_date += timedelta(days=1)
            return date_str