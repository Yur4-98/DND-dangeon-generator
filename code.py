import enum
import heapq
import random
import argparse
import collections
from matplotlib import pyplot

def randomColor():
    return '#' + str(random.randint(100000, 1000000))

def round(x, y, rad):
    points = set()
    for i in range(rad + 1):
        points.add((x + i, y - (rad - i)))
        points.add((x + i, y + (rad - i)))
        points.add((x - i, y - (rad - i)))
        points.add((x - i, y + (rad - i)))
    return points

def way(start, end, usedBlocks, maxWay):
    index = 0
    heap = [(0, index, start)]
    visitedPoints = {}
    while True:
        cost, _, point = heapq.heappop(heap)
        if maxWay <= cost:
            return None
        if point == end:
            return cost
        visitedPoints[point] = cost
        for nextPoint in point.near():
            if nextPoint in visitedPoints:
                continue
            if nextPoint in usedBlocks:
                continue
            index += 1
            heapq.heappush(heap, (cost + 1, index, nextPoint))
    return None


class DIRECTION(enum.Enum):
    L = 1
    R = 2
    U = 3
    D = 4

class Position:
    __slots__ = ('x', 'y')

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        return (self.x, self.y) == (other.x, other.y)

    def __ne__(self, other):
        return not self.__eq__(other)

    def near(self):
        return {Position(self.x - 1, self.y),
                Position(self.x, self.y - 1),
                Position(self.x + 1, self.y),
                Position(self.x, self.y + 1)}

    def area(self):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                yield Position(self.x + dx, self.y + dy)

    def move(self, dx, dy):
        return Position(self.x + dx, self.y + dy)

    def rotate(self):
        return Position(self.y, -self.x)

    def point(self):
        return (self.x, self.y)


class Border:
    __slots__ = ('pos', 'direct', 'internal', 'can_has_door', 'used')

    def __init__(self, pos, direct):
        self.pos = pos
        self.direct = direct
        self.internal = False
        self.can_has_door = False
        self.used = False

    def __eq__(self, other):
        return (self.pos, self.direct) == (other.pos, other.direct)

    def __ne__(self, other):
        return not self.__eq__(other)

    def mirror(self):
        if self.direct == DIRECTION.L:
            return Border(self.pos.move(-1, 0), DIRECTION.R)
        if self.direct == DIRECTION.R:
            return Border(self.pos.move(1, 0), DIRECTION.L)
        if self.direct == DIRECTION.U:
            return Border(self.pos.move(0, 1), DIRECTION.D)
        if self.direct == DIRECTION.D:
            return Border(self.pos.move(0, -1), DIRECTION.U)

    def geoBorders(self):
        if self.direct == DIRECTION.L:
            return [self.pos.move(0, 0).point(),
                    self.pos.move(0, 1).point()]
        if self.direct == DIRECTION.R:
            return [self.pos.move(1, 1).point(),
                    self.pos.move(1, 0).point()]
        if self.direct == DIRECTION.U:
            return [self.pos.move(0, 1).point(),
                    self.pos.move(1, 1).point()]
        if self.direct == DIRECTION.D:
            return [self.pos.move(1, 0).point(),
                    self.pos.move(0, 0).point()]

    def move(self, dx, dy):
        self.pos = self.pos.move(dx, dy)

    def rotate(self):
        self.pos = self.pos.rotate()
        if self.direct == DIRECTION.U:
            self.direct = DIRECTION.R
        elif self.direct == DIRECTION.R:
            self.direct = DIRECTION.D
        elif self.direct == DIRECTION.D:
            self.direct = DIRECTION.L
        else:
            self.direct = DIRECTION.U

    def connectPoint(self):
        segment = self.geoBorders()
        return ((segment[0][0] + segment[1][0]) / 2,
                (segment[0][1] + segment[1][1]) / 2)


class Block:
    __slots__ = ('pos', 'borders')

    def __init__(self, pos):
        self.pos = pos
        self.borders = {DIRECTION.R: Border(pos, DIRECTION.R),
                        DIRECTION.L: Border(pos, DIRECTION.L),
                        DIRECTION.U: Border(pos, DIRECTION.U),
                        DIRECTION.D: Border(pos, DIRECTION.D)}

    def geoBorders(self):
        return [border.geoBorders()
                for border in self.borders.values()
                if not border.internal]

    def syncBorders(self, block):
        for a in self.borders.values():
            for b in block.borders.values():
                if a.mirror() == b:
                    a.internal = True
                    b.internal = True

    def move(self, dx, dy):
        self.pos = self.pos.move(dx, dy)
        for border in self.borders.values():
            border.move(dx, dy)

    def rotate(self):
        self.pos = self.pos.rotate()
        for border in self.borders.values():
            border.rotate()
        self.borders = {border.direct: border for border in self.borders.values()}


class Room:
    __slots__ = ('blocks', 'color')

    def __init__(self):
        self.color = randomColor()
        self.blocks = [Block(Position(0, 0))]
 
    def blockPos(self):
        return {block.pos for block in self.blocks}

    def areaPos(self):
        area = set()
        for pos in self.blockPos():
            area |= set(pos.area())
        return area

    def newBlockPos(self):
        allowedPos = set()
        for block in self.blocks:
            allowedPos |= block.pos.near()
        allowedPos -= self.blockPos()
        return allowedPos

    def expand(self):
        newPos = random.choice(list(self.newBlockPos()))
        newBlock = Block(newPos)
        for block in self.blocks:
            block.syncBorders(newBlock)
        self.blocks.append(newBlock)

    def geoBorder(self):
        borders = []
        for block in self.blocks:
            borders.extend(block.geoBorders())
        return borders

    def rectangle(self):
        positions = self.blockPos()
        min_x, max_x, min_y, max_y = 0, 0, 0, 0
        for position in positions:
            max_x = max(position.x, max_x)
            max_y = max(position.y, max_y)
            min_x = min(position.x, min_x)
            min_y = min(position.y, min_y)
        return min_x, min_y, max_x, max_y  

    def intersection(self, room):
        return bool(self.areaPos() & room.blockPos())

    def move(self, dx, dy):
        for block in self.blocks:
            block.move(dx, dy)

    def rotate(self):
        for block in self.blocks:
            block.rotate()

    def borders(self):
        for block in self.blocks:
            for border in block.borders.values():
                yield border

    def BordersDoor(self):
        for border in self.borders():
            if border.can_has_door:
                yield border

    def makeDoors(self, number):
        borders = [border
                   for border in self.borders()
                   if not border.internal]
        number = min(len(borders), number)
        for border in random.sample(borders, number):
            border.can_has_door = True

class Corridor:
    __slots__ = ('start', 'stop')

    def __init__(self, start, stop):
        self.start = start
        self.stop = stop

    def segments(self):
        return [self.start.connectPoint(),
                self.stop.connectPoint()]


class Dungeon:
    __slots__ = ('rooms', 'corridors')

    def __init__(self):
        self.rooms = []
        self.corridors = []

    def createRoom(self, blocks, doors):
        room = Room()
        for i in range(blocks):
            room.expand()
        room.makeDoors(doors)
        return room

    def BordersDoor(self):
        for room in self.rooms:
            for border in room.BordersDoor():
                if not border.used:
                    yield border

    def intersection(self, room):
        return any(current_room.intersection(room) for current_room in self.rooms)

    def feetRoom(self, maxRadius, newRoom, dungeonpos):
        filledBlocks = {position.point() for position in dungeonpos}
        for maxDist in range(0, maxRadius):
            for dungeonDoor in self.BordersDoor():
                for doorNewRoom in newRoom.BordersDoor():
                    for x, y in round(*dungeonDoor.pos.point(), rad=maxDist):
                        if (x, y) in filledBlocks:
                            continue
                        for _ in range(4):
                            newRoom.rotate()
                            newRoom.move(x - doorNewRoom.mirror().pos.x,
                                          y - doorNewRoom.mirror().pos.y)
                            if self.intersection(newRoom):
                                continue
                            yield (maxDist, dungeonDoor, doorNewRoom, x, y)

    def blockPos(self):
        pos = set()
        for room in self.rooms:
            pos |= room.blockPos()
        return pos

    def expand(self, blocks, doors, maxRadius=17):
        newRoom = None
        while newRoom is None:
            newRoom = self.createRoom(blocks=blocks,
                                        doors=doors)
        if len(self.rooms) == 0:
            self.rooms.append(newRoom)
            return
        dungeonPos = self.blockPos()
        for maxDist, dungeonDoor, doorNewRoom, x, y in self.feetRoom(maxRadius,newRoom,dungeonPos):
            outDoor = dungeonDoor.mirror().pos
            newOutPos = doorNewRoom.mirror().pos
            filledPos = dungeonPos | newRoom.blockPos()
            realLength = way(outDoor,newOutPos,usedBlocks=filledPos,maxWay=maxDist)
            if realLength is None:
                continue
            break
        else:
            raise Exception('Can not place room')
        self.rooms.append(newRoom)
        newCorridor = Corridor(dungeonDoor, doorNewRoom)
        self.corridors.append(newCorridor)





dungeon = Dungeon()
for i in range(3):
    dungeon.expand(blocks=15,
                   doors=2)
for i in range(2):
    dungeon.expand(blocks=7,
                   doors=2)
for i in range(1):
    dungeon.expand(blocks=30,
                   doors=1)


pyplot.axes().set_aspect('equal', 'datalim')
fig = pyplot.figure(1)
for room in dungeon.rooms:
    for border in room.geoBorder():
        pyplot.plot(*zip(*border), color=room.color, linewidth=3, alpha=1.0)

for room in dungeon.rooms:
    for door_border in room.BordersDoor():
        pyplot.plot(*zip(*door_border.geoBorders()), color=room.color, linewidth=6, alpha=0)

for corridor in dungeon.corridors:
    pyplot.plot(*zip(*corridor.segments()), color='#000000', linewidth=1, alpha=1)

pyplot.show()
