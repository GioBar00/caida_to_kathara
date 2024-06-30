# Copyright 2014 ETH Zurich
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
:mod:`util` --- SCION utilities
===============================
"""
import math
import pathlib


def write_file(file_path, text):
    """
    Write some text into file, creating its directory as needed.
    :param str file_path: the path to the file.
    :param str text: the file content.
    """
    # ":" is an illegal filename char on both windows and OSX, so disallow it globally to prevent
    # incompatibility.
    assert ":" not in file_path, file_path

    pathlib.Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(file_path).write_text(text)


def symlink(source, dest, is_dir=False):
    """
    Create a symbolic link from source to dest, creating the directory as needed.
    :param str source: the source of the link.
    :param str dest: the destination of the link.
    """
    # ":" is an illegal filename char on both windows and OSX, so disallow it globally to prevent
    # incompatibility.
    assert ":" not in dest, dest

    pathlib.Path(dest).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(dest).symlink_to(source, target_is_directory=is_dir)


def calculate_great_circle_latency(lat1_deg, long1_deg, lat2_deg, long2_deg):
    distance = calculate_great_circle_distance(lat1_deg, long1_deg, lat2_deg, long2_deg)
    # 0.005 millisecods of latency per kilometer
    return distance * 0.005

def calculate_great_circle_distance(lat1_deg, long1_deg, lat2_deg, long2_deg):
    lat1 = math.radians(lat1_deg)
    long1 = math.radians(long1_deg)
    lat2 = math.radians(lat2_deg)
    long2 = math.radians(long2_deg)

    # Haversine formula
    dlat = lat2 - lat1
    dlong = long2 - long1

    distance = 2 * 6371 * math.asin(
        math.sqrt(
            math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlong / 2) ** 2
        )
    )

    return distance
