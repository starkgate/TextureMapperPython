import os
import shutil
import sqlite3
import csv

import numpy as np
from PIL import Image

from sqlite3 import Error
import argparse

parser = argparse.ArgumentParser(description='TextureMapper for the Mass Effect games')
parser.add_argument("--input", required=True, help="Path for the input csv", action="store")
parser.add_argument("--output", required=True, help="Path for the output textures", action="store")
parser.add_argument("--game", required=True, help="Game you want to port the textures to: 1-6 or ME1-LE3", action="store")
parser.add_argument("--no-name", help="Do not add texture name to ported filename", action="store_true")

args = parser.parse_args()

database = "textures_final.db"
init_textures_db = """create table textures (
    game integer,
    crc text,
    name text collate nocase,
    width integer,
    height integer,
    format text,
    primary key (game, crc)
);"""

"""
grade: 4-bit mask, grading the duplicate compared to the base texture
base texture is the highest res from the oldest game (ME1 < LE3)
identical to base?, resized?, different color?, different alpha?
"""
init_duplicates_db = """create table duplicates (
    groupid integer,
    game integer,
    crc text,
    grade integer,
    notes text,
    foreign key (game, crc) references textures(game, crc)
);"""

init_index1 = "create index index_crc_textures on textures (crc);"
init_index2 = "create index index_crc_duplicates on duplicates (crc);"
init_index3 = "create index index_groupid_game on duplicates (groupid, game);"


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object
    """
    try:
        return sqlite3.connect(db_file)
    except Error as e:
        print(e)
        exit()

conn = create_connection(database)
cur = conn.cursor()
"""
os.remove(database)

try:
    cur.execute(init_textures_db)
    cur.execute(init_duplicates_db)
    cur.execute(init_index1)
    cur.execute(init_index2)
    cur.execute(init_index3)
except Error as e:
    print(e)
print(cur.fetchall())

with open("texture_list.csv") as csv_file:
    rows = csv.reader(csv_file)
    next(rows, None) # skip first row: headers
    cur.executemany("INSERT INTO textures VALUES (?, ?, ?, ?, ?, ?)", rows)

with open("duplicates.csv") as csv_file:
    rows = csv.reader(csv_file)
    next(rows, None) # skip first row: headers
    cur.executemany("INSERT INTO duplicates VALUES (?, ?, ?, ?, ?)", rows)

conn.commit()
"""

def get_game_int(game):
    if game == "ME1":
        return 1
    elif game == "ME2":
        return 2
    elif game == "ME3":
        return 3
    elif game == "LE1":
        return 4
    elif game == "LE2":
        return 5
    elif game == "LE3":
        return 6
    else:
        raise Exception


def get_game_string(game):
    if game == 1:
        return "ME1"
    elif game == 2:
        return "ME2"
    elif game == 3:
        return "ME3"
    elif game == 4:
        return "LE1"
    elif game == 5:
        return "LE2"
    elif game == 6:
        return "LE3"
    else:
        raise Exception


if not os.path.isdir(args.output):
    os.makedirs(args.output)


def copy_duplicate(output_filename, row, stats_new):
    if not os.path.isfile(output_filename):
        shutil.copyfile(row[0], output_filename)
    else:
        try:
            stats_old = Image.open(output_filename).shape
        except:
            stats_old = cur.execute('SELECT height, width FROM textures WHERE crc = ? LIMIT 1', [dupe[2]]).fetchall()[0]

        if stats_new[0] > stats_old[0]:
            shutil.copyfile(row[0], output_filename)


with open(args.input) as csv_file:
    rows = csv.reader(csv_file)

    try:
        game = int(args.game)
    except:
        try:
            game = get_game_int(args.game)
        except:
            print('Wrong game input, must be 1-6 or ME1-LE3, exiting...')
            exit()

    for row in rows:
        filename = os.path.basename(row[0])
        name, crc = filename[:-15], filename[-14:-4]
        groupid = cur.execute('SELECT * FROM duplicates WHERE crc = ? LIMIT 1', [crc]).fetchall()

        if groupid:
            groupid = groupid[0]
            duplicates = cur.execute(
                "select d.game, t.name, d.crc, grade, notes, t.height, t.width from duplicates d "
                "join textures t on t.game = d.game and t.crc = d.crc "
                "where groupid = ? and d.game = ?", [groupid[0], game]).fetchall()
            for dupe in duplicates:
                grade = np.abs(int(groupid[3])-int(dupe[3]))
                print(f'{filename[:-4]} -> {dupe[1]}_{dupe[2]} with grade {grade}, format {dupe[4]}')
                try:
                    stats_new = Image.open(row[0]).size
                except:
                    stats_new = (0, 0)

                if args.no_name:
                    ported_filename = f'{dupe[2]}'
                else:
                    ported_filename = f'{dupe[1]}_{dupe[2]}'
                output_filename = os.path.join(
                    args.output, f'{ported_filename}-'
                                 f'van_{dupe[5]}x{dupe[6]}_{dupe[4]}-'
                                 f'dup_{stats_new[0]}x{stats_new[1]}_{groupid[4]}-'
                                 f'grade_{grade}.{filename[-3:]}'
                )

                copy_duplicate(output_filename, row, stats_new)
        else:
            dupe = cur.execute("select game, name, crc, height, width "
                               "from textures where crc = ? and game = ? limit 1", [crc, game]).fetchall()

            if dupe:
                dupe = dupe[0]
                print(f'{filename[:-4]} -> {dupe[1]}_{dupe[2]} with grade {0}, standalone')
                try:
                    stats_new = Image.open(row[0]).size
                except:
                    stats_new = (0, 0)

                if args.no_name:
                    ported_filename = f'{dupe[2]}'
                else:
                    ported_filename = f'{dupe[1]}_{dupe[2]}'
                output_filename = os.path.join(
                    args.output, f'{ported_filename}-'
                                 f'van_{dupe[3]}x{dupe[4]}-'
                                 f'dup_{stats_new[0]}x{stats_new[1]}-'
                                 f'grade_0.{filename[-3:]}'
                )

                copy_duplicate(output_filename, row, stats_new)

