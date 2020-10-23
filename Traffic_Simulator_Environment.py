import numpy as np
from typing import List

from Environment_Objects import Intersection, Road, Path, Car, Traffic_signal, Signals

UPDATE_DUR = 0.1
RENDER_DUR = 1
RL_UPDATE_DUR = 2

class Traffic_Simulator_Env():

    def __init__(self):
        ''' Initialize the environment. '''
        self.view = None
        self.scale = 1
        self.intersections = {}
        self.roads = {}
        self.paths = {}
        self.signals = []
        self.cars = []
        self.update_reward = 0

        self.update_reward = 0
        self.master_signals = []

        self.isRendering = False

        self.timer = 0

    def reset(self):
        ''' Rebuild the environment and reset all cars.\n
            Returns the initial state. '''
        self.intersections = {}
        self.roads = {}
        self.paths = {}

        self.signals = []
        self.timer = 0

        self.cars = []
        self.buildEnv()


        state = np.zeros((len(self.roads), 3), dtype=float)
        for key in self.roads:
            road = self.roads[key]
            state[road.number, 0] = road.get_car_density()
            state[road.number, 1] = road.get_mean_speed()
            state[road.number, 2] = road.get_trafficflow()
        return state

    def buildEnv(self):
        ''' Build the structures of the environment.\n
            Use addTrafficSignal(), addIntersection(), 
            addRoad(), addPath() in this method to 
            create your traffic system. '''

        self.sig1 = self.addTrafficSignal(Signals.RED, is_master=True)
        self.sig2 = self.addTrafficSignal(Signals.RED, is_master=False, master=self.sig1)
        self.action_space = len(self.master_signals)

        a = self.addIntersection("a", 0, 0)
        b = self.addIntersection("b", 200, 0)
        c = self.addIntersection("c", 400, 0)
        d = self.addIntersection("d", 200, -200)
        e = self.addIntersection("e", 200, 200)

        ab = self.addRoad(a, b, 60, self.sig1)
        bc = self.addRoad(b, c, 60)
        db = self.addRoad(d, b, 60, self.sig2)
        be = self.addRoad(b, e, 60)

        self.path1 = self.addPath([ab, bc], 1)
        self.path2 = self.addPath([db, be], 1)

    def toggleRender(self, enable, view):
        ''' Enable the rendering. \n
            Set the GraphicView Widget from PyQt for rendering. '''
        self.isRendering = enable
        self.view = view
        if not self.isRendering:
            for key in self.intersections:
                inte = self.intersections[key]
                if inte.graphicsItem != None:
                    self.view.scene.removeItem(inte.graphicsItem)
                    inte.graphicsItem = None
            for key in self.roads:
                road = self.roads[key]
                if road.graphicsItem != None:
                    self.view.scene.removeItem(road.graphicsItem)
                    road.graphicsItem = None
            for car in self.cars:
                if car.graphicsItem != None:
                    self.view.scene.removeItem(car.graphicsItem)
                    car.graphicsItem = None
            for ts in self.signals:
                if ts.graphicsItem != None:
                    self.view.scene.removeItem(ts.graphicsItem)
                    ts.graphicsItem = None

    def render(self, onlyNonStatic=False):
        if self.isRendering:
            if onlyNonStatic:
                self.renderNonStatic()
            else:
                self.renderStatic()
                self.renderNonStatic()

    def renderStatic(self):
        for key in self.intersections:
            inte = self.intersections[key]
            inte.render(self.view, self.scale)
        for key in self.roads:
            road = self.roads[key]
            road.render(self.view, self.scale)

    def renderNonStatic(self):
        for car in self.cars:
            car.render(self.view, self.scale)
        for ts in self.signals:
            ts.render(self.view, self.scale)

    def step_init(self):
        self.update_reward = 0

    def update(self):
        ''' Update the environment.'''
        self.timer = (self.timer * 10 + UPDATE_DUR * 10)/10
        rand1 = np.random.rand()
        rand2 = np.random.rand()
        if rand1 < 0.02:
            self.addCar(self.path1, maxSpd=20)
        if rand2 < 0.01:
            self.addCar(self.path2, maxSpd=20)
        for key in self.roads:
            self.roads[key].update()
        for index, car in enumerate(self.cars):
            car.update()
            if car.done:
                self.cars.pop(index)
        for sig in self.signals:
            sig.update()


    def makeAction(self, action):
        ''' Make an action, change the duration of the traffic signals. '''
        self.action = action
        for idx, master in enumerate(self.master_signals):
            master.change_duration(self.action[idx, 0], self.action[idx, 1])

    def getStateAndReward(self):
        ''' returns the current state, reward, terminal and info.  '''
        state_ = np.zeros((len(self.roads), 3), dtype=float)
        for key in self.roads:
            road = self.roads[key]
            state_[road.number, 0] = road.get_car_density()
            state_[road.number, 1] = road.get_mean_speed()
            state_[road.number, 2] = road.get_trafficflow()
        reward = self.update_reward
        term = None
        info = None
        return state_, reward, term, info 
        

    def addIntersection(self, name : str, x : int, y : int, diam =20):
        add = Intersection(name, x, -y, diam)
        self.intersections[add.name] = add
        return add

    def addRoad(self, start : Intersection, end : Intersection, spdLim : float, traffic_signal=None):
        name = start.name+"-"+end.name
        lim = spdLim/3600*1000
        add = Road(self, name, start, end, lim, traffic_signal=traffic_signal)
        add.number = len(self.roads)
        self.roads[add.name] = add
        return add

    def addPath(self, roads : List[Road], current : float):
        name = roads[0].name
        for i in range(len(roads) - 1):
            name += "," + roads[i+1].name
        add = Path(name, roads, current)
        return add

    def addTrafficSignal(self, def_signal, is_master=False, master=None):
        add = Traffic_signal(def_signal, update_dur=UPDATE_DUR, master=master)
        if is_master:
            self.master_signals.append(add)
        self.signals.append(add)
        return add

    def addCar(self, path : Path, maxSpd=20.0):
        add = Car(self, path, update_dur=UPDATE_DUR, maxSpd=maxSpd, view=self.view)
        self.cars.append(add)
        return add

         
        



    

