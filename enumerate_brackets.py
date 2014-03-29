#!/usr/bin/python

import csv, re, os

BRACKET = [('Florida', 'Dayton'),
           ('Michigan St.', 'UConn'),
           ('Arizona', 'Wisconsin'),
           ('Kentucky', 'Michigan')]

# Get all possible outcomes for a given bracket state (represented as a list of pairs).
def get_outcomes(curr_bracket):
  outcomes = []  

  # Trick: take all numbers from 0->2^n, look at them in binary to get the outcomes.
  for outcome in xrange(pow(2, len(curr_bracket))):
    fmt = '{0:0%db}' % (len(curr_bracket))
    picks = [ int(x) for x in fmt.format(outcome) ]
    outcomes.append([ game[0][game[1]] for game in zip(curr_bracket, picks) ])
  
  return outcomes

def play_round(curr_bracket):
  outcomes = get_outcomes(curr_bracket)
  # Collapse the winners to get the next round.
  new_brackets = [ zip(x[0::2], x[1::2]) for x in outcomes ]
  return (outcomes, new_brackets)

def get_all_outcomes():
  all_possibles = []

  (ee_outcomes, ff_brackets) = play_round(BRACKET)
  for ee_outcome, ff_bracket in zip(ee_outcomes, ff_brackets):
    (ff_outcomes, f_brackets) = play_round(ff_bracket)
    for ff_outcome, f_bracket in zip(ff_outcomes, f_brackets):
      all_possibles.append(ee_outcome + ff_outcome + [f_bracket[0][0]])
      all_possibles.append(ee_outcome + ff_outcome + [f_bracket[0][1]])

  return all_possibles

def extract_and_fetch_yahoo_bracket_urls():
  html = open('data/standings.html').read()
  url_re = re.compile('(?is)<a class="Fz-xss" href ="/quickenloansbracket/(\d+)">([^<]+)')
  for match in url_re.findall(html):
    url = 'https://tournament.fantasysports.yahoo.com/quickenloansbracket/%s' % match[0]
    filename = re.sub('\W+', '_', match[1])
    os.popen('wget -O data/bracket_%s "%s"' % (filename, url))

def extract_picks(filename):
  html = open(filename).read()
  points_re = re.compile('(?is)Final Foursquare</div></a>.*?<div class="Fl-end Grid-u">(\d+) pts<')
  points = points_re.search(html).group(1)
  pick_re = re.compile('(?is)id="g-(\d_\d+)-game">.*?-user-pick"><b><em>\d+</em> ([^<]+)')
  picks = pick_re.findall(html)
  pick_map = dict(picks)
  return [int(points), pick_map['1_1'], pick_map['2_1'], pick_map['3_1'], pick_map['4_1'],
          pick_map['0_2'], pick_map['0_3'], pick_map['0_1']]
         
def score_picks(picks, actual):
  POINTS = [8, 8, 8, 8, 16, 16, 32]
  def score(((pick, actual), points)):
    if pick == actual: return points
    else: return 0
  scores = [ score(x) for x in zip(zip(picks, actual), POINTS) ]
  return sum(scores)
  


if __name__ == '__main__':
  outcomes = get_all_outcomes()
  files = [ f.strip() for f in os.popen('ls data/bracket_*').readlines() ]
  brackets = [ (file[13:], extract_picks(file)) for file in files ]
  num_winners = dict.fromkeys([x[0] for x in brackets], 0)
  num_money = dict.fromkeys([x[0] for x in brackets], 0)

  outcomes_writer = csv.writer(open('data/outcomes.csv', 'wb'))
  outcomes_writer.writerow(['South', 'East', 'West', 'Midwest', 'Semi #1', 'Semi #2', 'Final',
                            '1st', '1st Points', '2nd', '2nd Points', '3rd', '3rd Points'])

  for outcome in outcomes:
    scores = [ (name, picks[0] + score_picks(picks[1:], outcome)) for (name, picks) in brackets ]
    ranked = sorted(scores, key=lambda s: s[1], reverse=True)
    outcomes_writer.writerow(outcome + list(ranked[0]) + list(ranked[1]) + list(ranked[2]))
    #print '%s: %s (%d)' % (str(outcome), ranked[0][0], ranked[0][1])
    num_winners[ranked[0][0]] += 1
    num_money[ranked[0][0]] += 1
    num_money[ranked[1][0]] += 1
    num_money[ranked[2][0]] += 1

  winners = sorted(num_winners.items(), key=lambda s: s[1], reverse=True)
  winners_writer = csv.writer(open('data/winners.csv', 'wb'))
  winners_writer.writerow(['Bracket', 'Ways to Win'])
  for w in winners:
    winners_writer.writerow(list(w))

  money = sorted(num_money.items(), key=lambda s: s[1], reverse=True)
  money_writer = csv.writer(open('data/money.csv', 'wb'))
  money_writer.writerow(['Bracket', 'Ways to Be in Top 3'])
  for m in money:
    money_writer.writerow(list(m))
