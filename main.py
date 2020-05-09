import csv
from datetime import datetime
import collections
from dataclasses import dataclass
import itertools
import functools 
def parse_date(d):
   return datetime.strptime(d, "%d/%m/%Y")

class Interval:
  def __init__(self, s, t):
    self.start = s
    self.end = t
  def intersect(lhs, rhs):
    return Interval(max(lhs.start, rhs.start), min(lhs.end, rhs.end))
  def valid(self):
    return self.start <= self.end


data = list(csv.DictReader(open("data.csv")))
for row in data:
  row["location"]   = row["Zone"] + "-" + row["MHE"] + "-" + row["wave_type"]
  row['start_unix'] = round(parse_date(row["Start_Date"]).timestamp())
  row['end_unix']   = round(parse_date(row["End_Date"]).timestamp())
  row['date_interval'] = Interval(row['start_unix'], row['end_unix'])
  row['max_patial'] = {
    "PalletJack": { "Single": 4400, "Multi": 3000, "Case": 5760 },
    "LiftTruck":  { "Single": 4400, "Multi": 2400, "Case": 5760 }
  }[row["MHE"]][row["wave_code"]]
  if row['max_patial'] is None:
    raise 'fuckk'
  row["wave_number"] = None
  row['patial'] = int(row['patial'])


@dataclass
class TrackBack:
  interval: Interval
  refs: list
  max_patial: int
  cur_patial: int

location = dict()
wave_count = 0
for row in sorted(data, key=lambda r: tuple([r["end_unix"], r['start_unix']])):
  head = location.get(row["location"], None)
  if head:
    new_patial = head.cur_patial + row['patial']
    new_interval = Interval.intersect(head.interval, row["date_interval"])
    if new_patial > head.max_patial or not new_interval.valid():
      wave_count += 1
      for r in head.refs:
        r["wave_number"] = wave_count
      del location[row["location"]]
      head = None
    else:
      head.cur_patial = new_patial
      head.interval = new_interval
      head.refs.append(row)
  if head is None:
    location[row["location"]] = TrackBack(row["date_interval"], [row], row["max_patial"], row['patial'])


for track in location.values():
  wave_count += 1
  for r in track.refs:
    r["wave_number"] = wave_count

with open('output.data.csv', 'w') as o:
  fieldnames = list(data[0].keys())
  writer = csv.DictWriter(o, fieldnames=fieldnames)
  writer.writeheader()
  for row in sorted(data, key=lambda r: r["wave_number"]):
    writer.writerow(row)

with open('output.logs.csv', 'w') as o:
  fn = lambda r: r["wave_number"]
  print('wave_number', 'items', 'patial', 'max_patial', 'date_start', 'date_end' 'zone', 'mhe', 'wave_type', sep=',', file=o)
  def fmt_date(stamp: int):
    return datetime.fromtimestamp(stamp).strftime("%d/%m/%Y")
  for wave, ls in itertools.groupby(sorted(data, key=fn), fn):
    ls = list(ls)
    date = functools.reduce(Interval.intersect, map(lambda r: r["date_interval"], ls))
    print(wave, len(ls), sum(map(lambda r: r["patial"], ls)), ls[0]["max_patial"], fmt_date(date.start), fmt_date(date.end), row["Zone"], row["MHE"], row["wave_type"], sep=',', file=o)