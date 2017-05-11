#c:\Python27\python.exe
from __future__ import division
import argparse, mechanize, cookielib, re, csv, pdb
from bs4 import BeautifulSoup as bs
Version = '0.3'

#############################################################
# A simple MWO stats scraper that dumps a specified users
# leaderboard stats to stdout and optionally a csv file.
#
# Script Requirements:
#   - Python 2.7 interpreter - https://www.python.org/downloads
#   - http://wwwsearch.sourceforge.net/mechanize
#      pip install mechanize
#   - https://pypi.python.org/pypi/beautifulsoup4
#      pip install bs4
#
# History
#   2016-09-21 / eta0h / V0.1 / Initial script
#   2016-12-26 / eta0h / V0.2 / Now defaults to current season,
#                               Added Jman5's Death Loss Ratio
#   2017-01-01 / eta0h / V0.3 / Now takes a list of pilots from the cmd line
#                               Now defaults to fetching all weight classes
#############################################################
# MWO username & password
Email = 'mwostats@gmail.com'
Password = 'fakepassword'

# Lists of pilot names you might want to track frequently
# call the script as -p "list"
lPilots = ['add', 'pilot-name', 'tothis', 'list']

########################################################
# Returns a dict comprised of the stats for a given
# pilot, season and all weight classes
########################################################
def FetchStats(Pilot, Season):
    
    dStats = {}
    
    # add cookie - avg match score
    stat_ck = cookielib.Cookie(version=0, name='leaderboard__rank_by', value='0', port=None,
        port_specified=False, domain='.mwomercs.com', domain_specified=False,
        domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None,
        discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
    cj.set_cookie(stat_ck)
        
    # add cookie - leaderboard season
    SeasonAdj = Season - 1
    season_ck = cookielib.Cookie(version=0, name='leaderboard_season', value='%i' % (SeasonAdj),
         port=None, port_specified=False, domain='.mwomercs.com', domain_specified=False,
        domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None,
        discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
    cj.set_cookie(season_ck)
    
    # Build up URL to reflect weight class and pilot
    for WC in ['global', 'light', 'medium', 'heavy', 'assault']:
        if WC == 'global': wctype = 0
        if WC == 'light': wctype = 1     
        if WC == 'medium': wctype = 2
        if WC == 'heavy': wctype = 3
        if WC == 'assault': wctype = 4
        StatsURL = 'https://mwomercs.com/profile/leaderboards?type=%i&user=%s' % (wctype, Pilot)
        
        # Send HTTP request
        page = br.open(StatsURL)
        soup = bs(page, 'html.parser')
        table = soup.find('table')
        
        # If season not specified, use current season
        if Season == 1000:
            Seasons = list(soup.find('select', id="season").stripped_strings)
            Season = int(Seasons[-1].split(" ")[1])
        
        # There may not be stats for the requested weight
        if re.search(r'No results found', str(table)): continue
        
        # Parse stats
        for row in soup('table')[0].findAll('tr'):
            col = row.findAll('td')
            if len(col) == 0: continue
            try:
                PilotName = col[1].string.encode('utf-8')
                if PilotName == Pilot:
                    dStats.update({WC: {
                        'Season': Season,
                        'Rank': int(col[0].string.encode('utf-8')),
                        'Wins': int(col[2].string.encode('utf-8')),
                        'Losses': int(col[3].string.encode('utf-8')),
                        'WLRatio': float(col[4].string.encode('utf-8')),
                        'Kills': int(col[5].string.encode('utf-8')),
                        'Deaths': int(col[6].string.encode('utf-8')),
                        'KDR': float(col[7].string.encode('utf-8')),
                        'GamesPlayed': int(col[8].string.encode('utf-8')),
                        'AvgScore': int(col[9].string.encode('utf-8'))
                    }})
                    break
                    
            except Exception, Error:
                print 'Something wicked happened - %s' % (Error)
                exit()
    return dStats

########################################################
# Main
########################################################
def main():
    
    global br, cj, Pilotlist, StatsFile, csvWriter
    
    # Arg parser
    parser = argparse.ArgumentParser(
        prog='lbstats.py',
        description='''A MWO leaderboard stats scraper that dumps a specified users
                       leaderboard stats to stdout and optionally a csv file.''',
        epilog='-----------------------------------------------------------------------',
        usage='''%(prog)s [options]"
        Examples:
          %(prog)s -p "JoePilot, Pilolt2, Pilot 3"
          %(prog)s -p JoePilot -s 3
          %(prog)s -p list -s 2 -f stats.csv''')
    
    # Arg Help
    parser.add_argument('-p', dest='Pilot', metavar='<PilotName>', required=True,
        help='''Required: Can be an individual pilot name, a comma delimited list of names
                or a list of pilots defined at the top of the script.
                The list is useful to track the same list of pilots, like all the pilots of a given unit.
                Use quotes for names with spaces and capitalization counts''')
    
    parser.add_argument('-f', dest='StatsFile', metavar='<FileName>', default=None,
        help='''Optional: The name of the csv file to dump the stats to.
                Default is to print to standard out only.''')
    
    parser.add_argument('-s', dest='Season', metavar='<Season>', default=1000 , type=int,
        help='Optional: The leaderboard season. Default is the current season')
    
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + Version)
    
    # Unpack args
    args = parser.parse_args()
    Pilot = args.Pilot
    Season = args.Season
    StatsFile = args.StatsFile
    
    # Open stats csv
    if StatsFile != None:
        try:
            csvStatsFile = open(StatsFile, 'wb', 0)
            csvWriter = csv.writer(csvStatsFile)
        except Exception, Error:
            print 'Unable to open stats file %s - %s' % (StatsFile, Error)
            exit()
            
    # Instantiate browser & cookie jar
    try:
        br = mechanize.Browser()
        cj = cookielib.LWPCookieJar('mwocookie')
        br.set_cookiejar(cj)
        br.open('https://mwomercs.com/login')
        br.select_form(nr=0)
        br['email'] = Email
        br['password'] = Password
        br.submit()
    except Exception, Error:
        print 'Unable to start browser - %s' % (Error)
        exit()
        
    # Log header stdio
    Templ = '{:^20} {:^7} {:^8} {:^6} {:^6} {:^6} {:^6}  {:^6}  {:^6}  {:^6} {:^8} {:^8} {:^8} {:^8}'
    print Templ.format('Pilot', 'Season', 'Weight', 'Rank', 'Wins', 'Losses', 'WLRatio',
                       'Kills', 'Deaths', 'KDRatio', 'Played', 'AvgScore', 'DLRatio', 'Kills/Game')
    # Log header csv
    if StatsFile != None:
        csvWriter.writerow(['Pilot', 'Season', 'Weight', 'Rank', 'Wins', 'Losses', 'WLRatio',
                            'Kills', 'Deaths', 'KDRatio', 'Played', 'AvgScore', 'DLRatio', 'KillsPerGame'])
        
    # Single pilot or list of pilots?
    Pilotlist = re.split(', |,',Pilot)
    if Pilot == 'list': Pilotlist = lPilots
    
    # Parse and dump stats
    for Pilot in Pilotlist:
        Stats = FetchStats(Pilot, Season)
        if Stats == False: continue
        
        if len(Stats) < 1:
             print 'Pilot name %s not found' % (Pilot)
             continue
             
        for WC in ['global', 'light', 'medium', 'heavy', 'assault']:
            if WC in Stats.keys():
                Season = Stats[WC]['Season']
                Rank = Stats[WC]['Rank']
                Wins = Stats[WC]['Wins']
                Losses = Stats[WC]['Losses']
                WLRatio = Stats[WC]['WLRatio']
                Kills = Stats[WC]['Kills']
                Deaths = Stats[WC]['Deaths']
                KDR = Stats[WC]['KDR']
                GamesPlayed = Stats[WC]['GamesPlayed']
                AvgScore = Stats[WC]['AvgScore']
                
                # DLR & KPG
                if Losses == 0:DLRatio = 0
                else: DLRatio = round(float(Deaths/Losses), 2)
                if Kills == 0: KillsPerGame = 0
                else: KillsPerGame = round(Kills/GamesPlayed, 2)
                
                print Templ.format(Pilot, Season, WC, Rank, Wins,
                   Losses, WLRatio, Kills, Deaths, KDR, GamesPlayed,
                   AvgScore, DLRatio, KillsPerGame)
                if StatsFile != None:
                    csvWriter.writerow([Pilot, Season, WC, Rank, Wins,
                    Losses, WLRatio, Kills, Deaths, KDR, GamesPlayed,
                    AvgScore, DLRatio, KillsPerGame])
                    
        print ''
        
    if StatsFile != None: print 'Success - stats saved to %s' % (StatsFile)
    
    return True
    
if __name__ == "__main__":
    main()
