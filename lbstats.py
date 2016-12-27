#c:\Python27\python.exe
from __future__ import division
import argparse, mechanize, cookielib, re, csv, pdb
from bs4 import BeautifulSoup as bs
Version = '0.2'

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
# Disclaimer
#   I am not a software dev and this code likely reflects that.
#   Feel free to use or improve as you like. Currently it fetches
#   stats serially and speed could be improved with concurrency.
#
# History
#   2016-09-21 / eta0h / V0.1 / Initial script
#   2016-12-26 / eta0h / V0.2 / Now defaults to current season,
#                               Added Death Loss Ratio
#############################################################
# MWO username & password
Email = 'name@somewhere.com'
Password = 'mypassword'

# List of pilot names you might want to track frequently
Pilotlist = ['Some Pilot', 'pilot2', 'Pilot 3']

########################################################
# Returns a dict comprised of the stats for a given
# pilot, season and all weight classes
########################################################
def FetchStats(Pilot, Season, Weight):
    
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
    
    if Weight == 'all':
        Weightlist = ['global', 'light', 'medium', 'heavy', 'assault']
    else:
        Weightlist = [Weight]
        
    # Build up URL to reflect weight class and pilot
    for WC in Weightlist:
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
        
        # If season not specified, re-map to current season
        if Season == 100:
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
                    Rank = int(col[0].string.encode('utf-8'))
                    Wins = int(col[2].string.encode('utf-8'))
                    Losses = int(col[3].string.encode('utf-8'))
                    WLRatio = float(col[4].string.encode('utf-8'))
                    Kills = int(col[5].string.encode('utf-8'))
                    Deaths = int(col[6].string.encode('utf-8'))
                    KDR = float(col[7].string.encode('utf-8'))
                    Played = int(col[8].string.encode('utf-8'))
                    AvgScore = int(col[9].string.encode('utf-8'))
                    if Losses == 0: DLRatio = 0
                    else: DLRatio = round(float(Deaths/Losses), 2)
                    dStats.update({WC: {
                        'Season': Season,
                        'Rank': Rank,
                        'Wins': Wins,
                        'Losses': Losses,
                        'WLRatio': WLRatio,
                        'Kills': Kills,
                        'Deaths': Deaths,
                        'KDR': KDR,
                        'GamesPlayed': Played,
                        'AvgScore': AvgScore,
                        'DLRatio': DLRatio
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
        description='''A simple MWO stats scraper that dumps a specified users
                       leaderboard stats to stdout and optionally a csv file.''',
        epilog='-----------------------------------------------------------------------',
        usage='''%(prog)s [options]"
        Examples:
          %(prog)s -p JoePilot -s 3
          %(prog)s -p "Joe Pilot" -w a
          %(prog)s -p list -s 2 -f stats.csv''')
    
    # Arg Help
    parser.add_argument('-p', dest='Pilot', metavar='<PilotName>', required=True,
        help='''Required: Can be an individual pilot name or the list of pilots defined at
                the top of the script. The list is useful to track the same list of pilots, like
                all the pilots of a given unit.
                Use quotes for spaces and capitalization counts''')
    
    parser.add_argument('-w', dest='Weight', metavar='<all|l|m|h|a>', default='all' ,
        choices=['all', 'g', 'l', 'm', 'h', 'a'],
        help='''Optional: The Mech weight class, where g=global, l=light, m=medium, h=heavy, a=assault.
                Default is to get all''')
    
    parser.add_argument('-f', dest='StatsFile', metavar='<FileName>', default=None,
        help='''Optional: The name of the csv file to dump the stats to.
                Default is to print to standard out only.''')
    
    parser.add_argument('-s', dest='Season', metavar='<Season>', default=100 , type=int,
        help='Optional: The leaderboard season. Default is latest')
    
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + Version)
    
    # Unpack args
    args = parser.parse_args()
    Pilot = args.Pilot
    Season = args.Season
    StatsFile = args.StatsFile
    Weight = args.Weight
    
    # Re-map weight class
    if Weight == 'g': Weight = 'global'
    if Weight == 'l': Weight = 'light'
    if Weight == 'm': Weight = 'medium'
    if Weight == 'h': Weight = 'heavy'
    if Weight == 'a': Weight = 'assault'
    
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
    Templ = '{:^20} {:^7} {:^8} {:^6} {:^6} {:^6} {:^6}  {:^6}  {:^6}  {:^6}  {:^8}  {:^8}  {:^8}'
    print Templ.format('Pilot', 'Season', 'Weight', 'Rank', 'Wins', 'Losses', 'WLRatio',
                       'Kills', 'Deaths', 'KDRatio', 'Played', 'AvgScore', 'DLRatio')
    # Log header csv
    if StatsFile != None:
        csvWriter.writerow(['Pilot', 'Season', 'Weight', 'Rank', 'Wins', 'Losses', 'WLRatio',
                            'Kills', 'Deaths', 'KDRatio', 'Played', 'AvgScore', 'DLRatio'])
        
    # Single pilot or list of pilots?
    if Pilot != 'list': Pilotlist = [Pilot]
    
    # Parse and dump stats
    for Pilot in Pilotlist:
        Stats = FetchStats(Pilot, Season, Weight)
        if Stats == False: continue
        
        if len(Stats) < 1:
             print 'Pilot name %s not found' % (Pilot)
             continue
             
        for WC in ['global', 'light', 'medium', 'heavy', 'assault']:
            if WC in Stats.keys():
                print Templ.format(Pilot, Stats[WC]['Season'], WC, Stats[WC]['Rank'], Stats[WC]['Wins'],
                   Stats[WC]['Losses'], Stats[WC]['WLRatio'], Stats[WC]['Kills'], Stats[WC]['Deaths'],
                   Stats[WC]['KDR'], Stats[WC]['GamesPlayed'], Stats[WC]['AvgScore'], Stats[WC]['DLRatio'])
                if StatsFile != None:
                    csvWriter.writerow([Pilot, Season, WC, Stats[WC]['Rank'], Stats[WC]['Wins'],
                    Stats[WC]['Losses'], Stats[WC]['WLRatio'], Stats[WC]['Kills'], Stats[WC]['Deaths'],
                    Stats[WC]['KDR'], Stats[WC]['GamesPlayed'], Stats[WC]['AvgScore'], Stats[WC]['DLRatio']])
        print ''
    if StatsFile != None:
        print 'Success - stats saved to %s' % (StatsFile)
        
    exit()
    
if __name__ == "__main__":
    main()
