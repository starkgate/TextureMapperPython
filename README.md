# TextureMapperPython
Semi-automatic porting of textures between the Mass Effect games (original and remastered)

**Requirements**
Python 3.x

**Installation**
Run `pip install numpy pillow pysqlite3`

**Usage**
```python texture_porter.py [-h] --input INPUT --output OUTPUT --game GAME```

For example: `python texture_porter.py  --input input.csv --output test_folder --game 1`
The input file must contain a list of the path of textures to port. Textures should contain their CRC at the end. Game can be either 1-6 or ME1-LE3.

The output files are named as follows: `{textureName}_{CRC}-van_{vanillaSize}_{channelFormat}-dup_{duplicateSize}_{channelFormat}-grade_{grade}.{format}`
The grade is an estimate of the difference between vanilla and dupe. 0 is perfect, anything else is different to some degree.
