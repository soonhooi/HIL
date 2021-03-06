#!/usr/bin/env python

import time

import aircraft
import sensors
from math import cos, sin, pi

class BasicAircraft(object):

    def __init__(self, attack=None):
        t_now = time.time()
        self.x = aircraft.State.default()
        self.u = aircraft.Controls.default()

        if attack == None:
            self.pressure = sensors.Pressure.default()
            self.imu = sensors.Imu.default()
            self.gps = sensors.Gps.default()
        else:
            import attack_sensors
            self.pressure = attack_sensors.AttackPressure.default()
            self.imu = attack_sensors.AttackImu.default()
            self.gps = attack_sensors.AttackGps.default()

        self.imu_period = 1.0/200;
        self.t_imu = t_now
        self.imu_count = 0

        self.gps_period = 1.0/10;
        self.t_gps = t_now
        self.gps_count = 0

        self.pressure_period = 1.0/10;
        self.t_pressure = t_now
        self.pressure_count = 0

        self.t_out = t_now

        self.attack = attack

        # test variables
        self.t0 = time.time()

    def update_state(self, fdm):
        self.x = aircraft.State.from_fdm(fdm)

    def update_state_test(self, sog, cog):
        t = time.time()
        dt = t - self.t0
        r_earth = 6378100
        vN = sog*cos(cog)
        vE = sog*sin(cog)
        vD = 0
        phi = 0
        theta = 0
        psi = cog
        latDot = vN/r_earth
        lat = latDot*dt
        lonDot = vE/r_earth/cos(lat)
        lon = lonDot*dt
        alt = 1000 -vD*dt
        self.x = aircraft.State(time = t,
            phi=phi, theta=theta, psi=psi,
            p=0, q=0, r=0,
            lat=lat, lon=lon, alt=alt,
            vN=vN, vE=vE, vD=vD, xacc=0, yacc=0, zacc=-9.806)
        #print 'latDot:', latDot, 'lonDot:', lonDot
        #print 'vN:', vN, 'vE:', vE, 'vD:', vD
        #print 'lat:', lat, 'lon:', lon, 'alt:', alt,
        #print 'phi:', phi, 'theta:', theta, 'psi:', psi

    def update_controls(self, m):
        self.u = aircraft.Controls.from_mavlink(m)

    def send_controls(self, jsb_console):
        self.u.send_to_jsbsim(jsb_console)

    def send_state(self, mav):
        self.x.send_to_mav(mav)

    def send_imu(self, mav):
        self.imu.from_state(self.x, self.attack)
        self.imu.send_to_mav(mav)

    def send_gps(self, mav):
        self.gps.from_state(self.x, self.attack)
        self.gps.send_to_mav(mav)

    def send_pressure(self, mav):
        self.pressure.from_state(self.x, self.attack)
        self.pressure.send_to_mav(mav)

    def send_sensors(self, mav):
        t_now = time.time()
        if t_now - self.t_gps > self.gps_period:
            self.t_gps = t_now
            self.send_gps(mav)
            self.gps_count += 1

        t_now = time.time()
        if t_now - self.t_imu > self.imu_period:
            self.t_imu = t_now
            self.send_imu(mav)
            self.imu_count += 1

        t_now = time.time()
        if t_now - self.t_pressure > self.pressure_period:
            self.t_pressure = t_now
            self.send_pressure(mav)
            self.pressure_count += 1

        t_now = time.time()
        if t_now - self.t_out > 1:
            self.t_out = t_now
            print 'imu {0:4d} Hz, gps {1:4d} Hz, pressure {2:4d} Hz\n'.format(
                self.imu_count, self.gps_count, self.pressure_count)
            self.gps_count = 0
            self.imu_count = 0
            self.pressure_count = 0

