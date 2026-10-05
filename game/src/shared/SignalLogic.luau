--!strict
-- How signal devices decide whether they are on. The whole rule:
--
--   1. Every signal device is either on or off.
--   2. Four kinds decide for themselves ("sources"): a switch is on when it has been flipped on, a
--      sensor while an item is on it, a timer for the first half of each cycle, a counter for a
--      moment each time enough items have passed.
--   3. Three kinds look at the signal devices touching them (the six cells around them):
--        logic box  "and": on when it touches at least one sender and all of them are on
--                   "or":  on when any sender it touches is on
--                   "not": on when no sender it touches is on
--        gate       open when any sender it touches is on (or the reverse, if set to rest open)
--        beacon     lit when any sender it touches is on
--      A "sender" is a source or a logic box. Gates and beacons only receive.
--   4. Ordinary machines touching signal devices:
--        - they are "signalled" while any sender touching them is on (the pusher uses this);
--        - a machine touching a switch, a timer or a logic box runs only while at least one of
--          those is on. Sensors and counters never stop a machine by themselves: put a logic box
--          between them and the machine.
--
--   5. A device that needs electricity and has none is off, whatever it touches or sees.
--
-- Devices read what their neighbours were a moment ago, so a chain of logic boxes settles one box
-- per beat instead of all at once, and loops cannot hang.
local SignalLogic = {}

export type Node = {
	kind: string,
	on: boolean, -- what it was after the last step
	raw: boolean?, -- for sources: what they decide for themselves right now
	mode: string?, -- for logic boxes
	invert: boolean?, -- for gates: rest open
	dead: boolean?, -- needs electricity and has none
	links: { number }, -- indexes of the signal devices touching this one
}

local SENDERS = { switch = true, sensor = true, timer = true, counter = true, logic = true }
local SOURCES = { switch = true, sensor = true, timer = true, counter = true }
local CONTROLLERS = { switch = true, timer = true, logic = true }

SignalLogic.KINDS = { "switch", "sensor", "timer", "counter", "logic", "gate", "beacon" }
SignalLogic.MODES = { "and", "or", "not" }
SignalLogic.PERIODS = { 2, 5, 10, 30 } -- seconds a timer's cycle can be set to
SignalLogic.TARGETS = { 5, 10, 20, 50 } -- how many items a counter can be set to wait for
SignalLogic.PULSE = 1 -- seconds a counter stays on when it fires

function SignalLogic.isSender(kind: string): boolean
	return SENDERS[kind] == true
end

function SignalLogic.isController(kind: string): boolean
	return CONTROLLERS[kind] == true
end

-- One beat: what every device is now, given what each was.
function SignalLogic.step(nodes: { Node }): { boolean }
	local result: { boolean } = table.create(#nodes, false)
	for i, node in nodes do
		if node.dead then
			result[i] = false
			continue
		end
		if SOURCES[node.kind] then
			result[i] = node.raw == true
			continue
		end
		local senders, lit = 0, 0
		for _, link in node.links do
			local other = nodes[link]
			if other and SENDERS[other.kind] then
				senders += 1
				if other.on then
					lit += 1
				end
			end
		end
		if node.kind == "logic" then
			if node.mode == "and" then
				result[i] = senders > 0 and lit == senders
			elseif node.mode == "not" then
				result[i] = lit == 0
			else
				result[i] = lit > 0
			end
		elseif node.kind == "gate" then
			result[i] = (lit > 0) ~= (node.invert == true)
		else
			result[i] = lit > 0
		end
	end
	return result
end

-- What an ordinary machine is told, given the states of the senders touching it and, separately,
-- of the controllers among them. Returns signalled, halted.
function SignalLogic.forMachine(senders: { boolean }, controllers: { boolean }): (boolean, boolean)
	local signalled = table.find(senders, true) ~= nil
	local halted = #controllers > 0 and table.find(controllers, true) == nil
	return signalled, halted
end

-- A timer is on for the first half of its cycle.
function SignalLogic.timerOn(elapsed: number, period: number): boolean
	return elapsed % period < period / 2
end

-- Adds the items that just passed. Returns the new count and whether the counter fires; when it
-- fires, the target is taken off and the remainder carries over.
function SignalLogic.count(count: number, target: number, passed: number): (number, boolean)
	local total = count + passed
	if total >= target then
		return total % target, true
	end
	return total, false
end

-- The entry after `current` in a list, wrapping round. Anything not in the list gives the first.
function SignalLogic.nextOf<T>(list: { T }, current: T): T
	local index = table.find(list, current) or 0
	return list[index % #list + 1]
end

local function whole(n: any, least: number, most: number, fallback: number): number
	if type(n) == "number" and n == n and n >= least and n <= most then
		return math.floor(n)
	end
	return fallback
end

-- A device's settings rebuilt from stored data, with anything missing or odd replaced by the
-- setting a newly placed device has. `isItem` checks a sensor's stored condition.
function SignalLogic.sanitize(kind: string, raw: any, isItem: (any) -> boolean): { [string]: any }
	local saved: { [string]: any } = if type(raw) == "table" then raw else {}
	if kind == "switch" then
		return { on = saved.on == true }
	elseif kind == "timer" then
		local period = if table.find(SignalLogic.PERIODS, saved.period)
			then saved.period
			else SignalLogic.PERIODS[2]
		return { period = period, t = whole(saved.t, 0, period, 0) }
	elseif kind == "logic" then
		return { mode = if table.find(SignalLogic.MODES, saved.mode) then saved.mode else "or" }
	elseif kind == "gate" then
		return { invert = saved.invert == true }
	elseif kind == "counter" then
		local target = if table.find(SignalLogic.TARGETS, saved.target)
			then saved.target
			else SignalLogic.TARGETS[2]
		return { target = target, count = whole(saved.count, 0, target - 1, 0) }
	elseif kind == "sensor" then
		return { filter = if isItem(saved.filter) then saved.filter else nil }
	end
	return {}
end

return SignalLogic
