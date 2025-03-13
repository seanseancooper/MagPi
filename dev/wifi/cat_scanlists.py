import os
import json
import glob

scanlists = glob.glob('/Users/scooper/PycharmProjects/MagPi/_out' + "/*.json")
data = []   # lists of lists of maps
output_map = {}
for scanlist in scanlists:
    with open(scanlist, "r") as f:
        data.append(json.load(f))

print(data)

for scanlist in data:
    for signal in scanlist:
        output_map[signal['BSSID']] = signal

print(json.dumps(output_map))

ids = [_ for _ in output_map]
with open('./scanlists_out.json', 'w') as f:
    for id in ids:
        f.write(json.dumps(output_map[id])+'\n')
