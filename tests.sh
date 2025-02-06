python -m app.main decode i52e
python -m app.main decode 6:orange
python -m app.main decode lli877e6:bananaee
python -m app.main decode d3:foo3:bar5:helloi52ee
python -m app.main decode d3:foo9:blueberry5:helloi52ee

python -m app.main info sample.torrent

python -m app.main peers sample.torrent

python -m app.main handshake sample.torrent 165.232.38.164:51493

python -m app.main download_piece -o ./test-piece sample.torrent 1

python -m app.main download -o ./test.txt sample.torrent

python -m app.main magnet_parse "magnet:?xt=urn:btih:ad42ce8109f54c99613ce38f9b4d87e70f24a165&dn=magnet1.gif&tr=http%3A%2F%2Fbittorrent-test-tracker.codecrafters.io%2Fannounce"
