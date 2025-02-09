from aiogram import Router
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from datetime import datetime

import pytz
import database as db
import keyboard as kb

router = Router()

