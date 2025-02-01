python3 -m app.main decode i52e
python3 -m app.main decode 6:orange
python3 -m app.main decode lli877e6:bananaee
python3 -m app.main decode d3:foo3:bar5:helloi52ee
python3 -m app.main decode d3:foo9:blueberry5:helloi52ee

python3 -m app.main info sample.torrent

python -m app.main peers sample.torrent

python3 -m app.main handshake sample.torrent 165.232.38.164:51493

python3 -m app.main download_piece -o ./test-piece sample.torrent 1
