-- Devices: signals, movers and farm machines.  lune run tests/devices_test.luau
local T = require("./harness")
local SignalLogic = require("../src/shared/SignalLogic")
local MoverLogic = require("../src/shared/MoverLogic")
local FarmLogic = require("../src/shared/FarmLogic")
local Defs = require("../src/shared/Defs")

local test, eq = T.test, T.eq

local function node(kind: string, on: boolean, links: { number }, extra: any?): any
	local made = { kind = kind, on = on, links = links, raw = nil, mode = nil, invert = nil }
	for key, value in extra or {} do
		made[key] = value
	end
	return made
end

-- Signals
test("sources are whatever they decide for themselves", function()
	local result = SignalLogic.step({
		node("switch", false, {}, { raw = true }),
		node("sensor", true, {}, { raw = false }),
		node("timer", false, {}, { raw = true }),
		node("counter", false, {}),
	})
	eq(result[1], true)
	eq(result[2], false)
	eq(result[3], true)
	eq(result[4], false)
end)
test("a gate opens when a sender touching it is on, and a resting-open gate does the reverse", function()
	local function gate(switchOn: boolean, invert: boolean): boolean
		return SignalLogic.step({
			node("switch", switchOn, { 2 }, { raw = switchOn }),
			node("gate", false, { 1 }, { invert = invert }),
		})[2]
	end
	eq(gate(true, false), true)
	eq(gate(false, false), false)
	eq(gate(true, true), false)
	eq(gate(false, true), true)
	-- with nothing touching it, a gate is shut unless it rests open
	eq(SignalLogic.step({ node("gate", false, {}) })[1], false)
	eq(SignalLogic.step({ node("gate", false, {}, { invert = true }) })[1], true)
end)
test("gates and beacons do not pass a signal on", function()
	local result = SignalLogic.step({
		node("gate", true, { 2 }),
		node("beacon", false, { 1, 3 }),
		node("beacon", true, { 2 }),
	})
	eq(result[2], false)
	eq(result[3], false)
end)
test("a logic box combines the senders touching it", function()
	local function logic(mode: string, a: boolean, b: boolean): boolean
		return SignalLogic.step({
			node("switch", a, { 3 }, { raw = a }),
			node("sensor", b, { 3 }, { raw = b }),
			node("logic", false, { 1, 2 }, { mode = mode }),
		})[3]
	end
	eq(logic("and", true, true), true)
	eq(logic("and", true, false), false)
	eq(logic("or", false, true), true)
	eq(logic("or", false, false), false)
	eq(logic("not", false, false), true)
	eq(logic("not", true, false), false)
end)
test("a logic box touching nothing is off, unless it is set to not", function()
	eq(SignalLogic.step({ node("logic", false, {}, { mode = "and" }) })[1], false)
	eq(SignalLogic.step({ node("logic", false, {}, { mode = "or" }) })[1], false)
	eq(SignalLogic.step({ node("logic", false, {}, { mode = "not" }) })[1], true)
end)
test("a signal crosses one logic box per beat", function()
	local nodes = {
		node("switch", false, { 2 }, { raw = true }),
		node("logic", false, { 1, 3 }, { mode = "or" }),
		node("logic", false, { 2, 4 }, { mode = "or" }),
		node("beacon", false, { 3 }),
	}
	local function beat()
		local result = SignalLogic.step(nodes)
		for i, on in result do
			nodes[i].on = on
		end
	end
	beat()
	eq(nodes[1].on, true)
	eq(nodes[2].on, false)
	beat()
	eq(nodes[2].on, true)
	eq(nodes[3].on, false)
	beat()
	eq(nodes[3].on, true)
	eq(nodes[4].on, false)
	beat()
	eq(nodes[4].on, true)
end)
test("two not-boxes facing each other keep flipping and never hang", function()
	local nodes =
		{ node("logic", false, { 2 }, { mode = "not" }), node("logic", false, { 1 }, { mode = "not" }) }
	local seen = {}
	for _ = 1, 6 do
		local result = SignalLogic.step(nodes)
		nodes[1].on, nodes[2].on = result[1], result[2]
		table.insert(seen, result[1])
	end
	eq(seen[1], true)
	eq(seen[2], false)
	eq(seen[3], true)
end)
test("a device without the electricity it needs is off, and passes nothing on", function()
	local result = SignalLogic.step({
		node("timer", true, { 2 }, { raw = true, dead = true }),
		node("gate", true, { 1 }, { invert = true, dead = true }),
		node("logic", true, {}, { mode = "not", dead = true }),
	})
	eq(result[1], false)
	eq(result[2], false)
	eq(result[3], false)
	-- a dead sender reads as off to a live neighbour on the next beat
	local nodes = { node("timer", false, { 2 }, { raw = true, dead = true }), node("beacon", false, { 1 }) }
	eq(SignalLogic.step(nodes)[2], false)
end)
test("a link to a device that is not there is ignored", function()
	eq(SignalLogic.step({ node("beacon", false, { 7 }) })[1], false)
end)
test("machines are signalled by any sender but stopped only by controllers", function()
	local signalled, halted = SignalLogic.forMachine({ true }, {})
	eq(signalled, true)
	eq(halted, false)
	-- a sensor that is off does not stop the machine next to it
	signalled, halted = SignalLogic.forMachine({ false }, {})
	eq(signalled, false)
	eq(halted, false)
	-- a switch that is off does
	signalled, halted = SignalLogic.forMachine({ false }, { false })
	eq(halted, true)
	-- one controller on is enough to run
	signalled, halted = SignalLogic.forMachine({ false, true }, { false, true })
	eq(signalled, true)
	eq(halted, false)
	signalled, halted = SignalLogic.forMachine({}, {})
	eq(signalled, false)
	eq(halted, false)
end)
test("only switches, timers and logic boxes are controllers; gates and beacons send nothing", function()
	eq(SignalLogic.isController("switch"), true)
	eq(SignalLogic.isController("timer"), true)
	eq(SignalLogic.isController("logic"), true)
	eq(SignalLogic.isController("sensor"), false)
	eq(SignalLogic.isController("counter"), false)
	eq(SignalLogic.isSender("sensor"), true)
	eq(SignalLogic.isSender("gate"), false)
	eq(SignalLogic.isSender("beacon"), false)
end)
test("a timer is on for the first half of each cycle", function()
	eq(SignalLogic.timerOn(0, 10), true)
	eq(SignalLogic.timerOn(4.9, 10), true)
	eq(SignalLogic.timerOn(5, 10), false)
	eq(SignalLogic.timerOn(9.9, 10), false)
	eq(SignalLogic.timerOn(10, 10), true)
end)
test("a counter fires when enough have passed and carries the rest over", function()
	local count, fired = SignalLogic.count(3, 10, 4)
	eq(count, 7)
	eq(fired, false)
	count, fired = SignalLogic.count(7, 10, 3)
	eq(count, 0)
	eq(fired, true)
	-- a whole stack passing at once
	count, fired = SignalLogic.count(8, 10, 5)
	eq(count, 3)
	eq(fired, true)
	count, fired = SignalLogic.count(0, 5, 0)
	eq(fired, false)
end)
test("settings cycle through their choices", function()
	eq(SignalLogic.nextOf(SignalLogic.MODES, "and"), "or")
	eq(SignalLogic.nextOf(SignalLogic.MODES, "not"), "and")
	eq(SignalLogic.nextOf(SignalLogic.PERIODS, 30), 2)
	eq(SignalLogic.nextOf(SignalLogic.TARGETS, 999), SignalLogic.TARGETS[1])
end)
test("stored settings are cleaned on load", function()
	eq(SignalLogic.sanitize("switch", { on = true }, Defs.isItem).on, true)
	eq(SignalLogic.sanitize("switch", { on = "yes" }, Defs.isItem).on, false)
	eq(SignalLogic.sanitize("switch", "junk", Defs.isItem).on, false)
	local timer = SignalLogic.sanitize("timer", { period = 7, t = 0 / 0 }, Defs.isItem)
	eq(timer.period, 5)
	eq(timer.t, 0)
	eq(SignalLogic.sanitize("timer", { period = 30, t = 12.7 }, Defs.isItem).t, 12)
	eq(SignalLogic.sanitize("logic", { mode = "xor" }, Defs.isItem).mode, "or")
	eq(SignalLogic.sanitize("logic", { mode = "not" }, Defs.isItem).mode, "not")
	eq(SignalLogic.sanitize("gate", nil, Defs.isItem).invert, false)
	local counter = SignalLogic.sanitize("counter", { target = 20, count = 99 }, Defs.isItem)
	eq(counter.target, 20)
	eq(counter.count, 0)
	eq(SignalLogic.sanitize("counter", { target = 20, count = 19 }, Defs.isItem).count, 19)
	eq(SignalLogic.sanitize("sensor", { filter = "ingot_fe" }, Defs.isItem).filter, "ingot_fe")
	eq(SignalLogic.sanitize("sensor", { filter = "banana" }, Defs.isItem).filter, nil)
	eq(next(SignalLogic.sanitize("beacon", { anything = 1 }, Defs.isItem)), nil)
end)
test("every signal device in the game is a kind the rules know", function()
	local count = 0
	for id, def in Defs.Machines do
		if def.behavior == "signal" then
			count += 1
			assert(table.find(SignalLogic.KINDS, def.signal), id .. " is an unknown kind of signal device")
		end
	end
	eq(count, #SignalLogic.KINDS)
end)

-- Movers
local function landing(speed: number, angle: number, gravity: number, distance: number): number
	-- height when the thrown thing has travelled `distance` along the ground
	local t = distance / (speed * math.cos(angle))
	return speed * math.sin(angle) * t - gravity * t * t / 2
end
test("a thrown item comes down where it was aimed", function()
	for _, case in { { 5, -4.9 }, { 17, -4.9 }, { 8, 3 }, { 11, 0 } } do
		local distance, rise = case[1], case[2]
		local speed = MoverLogic.launchSpeed(distance, rise, 196.2, math.rad(45)) :: number
		assert(
			math.abs(landing(speed, math.rad(45), 196.2, distance) - rise) < 1e-6,
			"missed at distance " .. distance
		)
	end
end)
test("a throw that the angle cannot reach is refused", function()
	-- straight up a wall: 10 studs higher only 5 away, at 45 degrees
	eq(MoverLogic.launchSpeed(5, 10, 196.2, math.rad(45)), nil)
	eq(MoverLogic.launchSpeed(0, -1, 196.2, math.rad(45)), nil)
	eq(MoverLogic.launchSpeed(-3, -1, 196.2, math.rad(45)), nil)
end)
test("further targets need a harder throw", function()
	local near = MoverLogic.launchSpeed(5, -4.9, 196.2, math.rad(45)) :: number
	local far = MoverLogic.launchSpeed(17, -4.9, 196.2, math.rad(45)) :: number
	assert(far > near, "the far throw was not harder")
end)
test("a blower pushes at full strength up close and fades to nothing at the end of its range", function()
	eq(MoverLogic.blow(30, 0, 9), 30)
	eq(MoverLogic.blow(30, 3, 9), 30)
	eq(MoverLogic.blow(30, 6, 9), 15)
	eq(MoverLogic.blow(30, 9, 9), 0)
	eq(MoverLogic.blow(30, 20, 9), 0)
	eq(MoverLogic.blow(30, -1, 9), 0)
end)

-- Farm
local function world(cells: { [string]: string })
	local function at(x: number, y: number, z: number): string?
		return cells[x .. "," .. y .. "," .. z]
	end
	return function(x: number, y: number, z: number): boolean
		return at(x, y, z) == "log"
	end, function(x: number, y: number, z: number): boolean
		return at(x, y, z) == "leaves"
	end
end
local function plant(cells: { [string]: string }, x: number, base: number, z: number, height: number)
	for y = base, base + height - 1 do
		cells[x .. "," .. y .. "," .. z] = "log"
	end
	local top = base + height - 1
	for dy = 0, 1 do
		for dx = -1, 1 do
			for dz = -1, 1 do
				if not (dx == 0 and dz == 0 and dy == 0) then
					cells[(x + dx) .. "," .. (top + dy) .. "," .. (z + dz)] = "leaves"
				end
			end
		end
	end
	cells[x .. "," .. (top + 2) .. "," .. z] = "leaves"
end
test("a logger takes the nearest tree from the top down", function()
	local cells = {}
	plant(cells, 2, 1, 0, 3)
	plant(cells, -3, 1, 3, 4)
	local isLog = world(cells)
	local first = FarmLogic.nextLog(isLog, 0, 1, 0, 3, 1, 8) :: any
	eq(first.x, 2)
	eq(first.y, 3)
	eq(first.z, 0)
	cells["2,3,0"] = nil
	eq((FarmLogic.nextLog(isLog, 0, 1, 0, 3, 1, 8) :: any).y, 2)
	cells["2,2,0"] = nil
	cells["2,1,0"] = nil
	-- the near tree is gone, so it moves on to the far one
	local nextTree = FarmLogic.nextLog(isLog, 0, 1, 0, 3, 1, 8) :: any
	eq(nextTree.x, -3)
	eq(nextTree.y, 4)
end)
test("a logger ignores trees out of reach and the cell it stands in", function()
	local cells = {}
	plant(cells, 5, 1, 0, 3)
	cells["0,1,0"] = "log"
	local isLog = world(cells)
	eq(FarmLogic.nextLog(isLog, 0, 1, 0, 3, 1, 8), nil)
	eq((FarmLogic.nextLog(isLog, 0, 1, 0, 5, 1, 8) :: any).x, 5)
end)
test("a trunk stands while any log of it is left", function()
	local cells = { ["1,2,1"] = "log" }
	local isLog = world(cells)
	eq(FarmLogic.trunkStands(isLog, 1, 1, 0, 6), true)
	eq(FarmLogic.trunkStands(isLog, 1, 1, 3, 6), false)
	eq(FarmLogic.trunkStands(isLog, 2, 1, 0, 6), false)
end)
test("when a tree is cut down all its leaves go, and a neighbouring tree keeps its own", function()
	local cells = {}
	plant(cells, 0, 1, 0, 3)
	plant(cells, 6, 1, 0, 3)
	local isLog, isLeaf = world(cells)
	for y = 1, 3 do
		cells["0," .. y .. ",0"] = nil
	end
	local loose = FarmLogic.looseLeaves(isLeaf, isLog, 0, 1, 0)
	eq(#loose, 18) -- 8 around the top log, 9 above it, 1 on the very top
	for _, leaf in loose do
		assert(leaf.x <= 1, "took a leaf from the other tree")
	end
end)
test("leaves shared with a tree that still stands are left alone", function()
	local cells = {}
	plant(cells, 0, 1, 0, 3)
	plant(cells, 2, 1, 0, 3)
	local isLog, isLeaf = world(cells)
	for y = 1, 3 do
		cells["0," .. y .. ",0"] = nil
	end
	for _, leaf in FarmLogic.looseLeaves(isLeaf, isLog, 0, 1, 0) do
		assert(leaf.x < 0, "took a leaf within reach of the standing tree at x = " .. leaf.x)
	end
end)
test("the nearest fitting cell is found on the machine's own level, never its own cell", function()
	local plots = { ["2,0"] = true, ["-1,1"] = true, ["0,0"] = true }
	local function fits(x: number, y: number, z: number): boolean
		return y == 4 and plots[x .. "," .. z] == true
	end
	local found = FarmLogic.nearest(fits, 0, 4, 0, 2) :: any
	eq(found.x, -1)
	eq(found.z, 1)
	plots["-1,1"] = nil
	eq((FarmLogic.nearest(fits, 0, 4, 0, 2) :: any).x, 2)
	plots["2,0"] = nil
	eq(FarmLogic.nearest(fits, 0, 4, 0, 2), nil)
	eq(FarmLogic.nearest(fits, 0, 5, 0, 2), nil)
end)

-- The data the devices rely on
test("what the farm machines handle exists", function()
	assert(
		Defs.isItem("log") and Defs.isItem("seed") and Defs.isItem("wheat") and Defs.isItem("sapling"),
		"an item is missing"
	)
	assert(Defs.isBlock("log") and Defs.isBlock("leaves") and Defs.isBlock("farmland"), "a block is missing")
	eq(Defs.Machines.crop_wheat_1.cost, "seed")
	eq(Defs.Machines.plant_sapling.behavior, "sapling")
end)
test("each device has the mouths its code expects", function()
	local function mouths(id: string): (number, number)
		local ins, outs = 0, 0
		for _, port in Defs.Machines[id].ports do
			if port.kind == "in" then
				ins += 1
			else
				outs += 1
			end
		end
		return ins, outs
	end
	for id, want in
		{
			lift = { 1, 0 },
			launcher = { 1, 0 },
			pusher = { 1, 2 },
			logger = { 0, 1 },
			harvester = { 0, 1 },
			seeder = { 1, 0 },
		}
	do
		local ins, outs = mouths(id)
		eq(ins, want[1], id .. " inputs")
		eq(outs, want[2], id .. " outputs")
	end
	-- the pusher's straight-on mouth comes first, its side mouth second
	eq(Defs.Machines.pusher.ports[2].side, "E")
	eq(Defs.Machines.pusher.ports[3].side, "S")
	eq(Defs.Machines.belt_ramp.sx, 2)
	eq(Defs.Machines.chute.sx, 2)
	eq(Defs.Machines.chest.topIntake, true)
end)

T.done()
