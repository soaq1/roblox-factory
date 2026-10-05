--!strict
-- What a processing machine decides, separate from how it looks. Items go into a buffer; when the
-- buffer holds everything a recipe needs, the machine works for a while and the results wait in an
-- output buffer until they are taken.
local ProcessLogic = {}

export type Recipe = { ins: { [string]: number }, outs: { [string]: number }, secs: number }
export type Rules = {
	recipes: { Recipe },
	usesFuel: boolean,
	fuel: { [string]: number }, -- item id -> how many jobs one unit pays for
	cap: number, -- most of one item the input buffer holds
	outCap: number, -- most items waiting in the output buffer before work pauses
	-- Optional. Items whose buffer holds a different amount from `cap`; see ProcessLogic.caps.
	caps: { [string]: number }?,
	-- Optional. Fuel one job uses, when not 1. A machine on electricity uses less.
	fuelPerJob: number?,
}
export type State = {
	buf: { [string]: number },
	out: { [string]: number },
	fuel: number,
	progress: number,
}

function ProcessLogic.new(): State
	return { buf = {}, out = {}, fuel = 0, progress = 0 }
end

-- Buffer sizes for ingredients that a recipe needs more of than `cap` holds, so that every recipe
-- can actually be filled. A recipe that takes 2000 of something gets room for 2000 of it.
function ProcessLogic.caps(recipes: { Recipe }, cap: number): { [string]: number }
	local caps: { [string]: number } = {}
	for _, recipe in recipes do
		for id, n in recipe.ins do
			if n > cap and n > (caps[id] or 0) then
				caps[id] = n
			end
		end
	end
	return caps
end

local function capOf(itemId: string, rules: Rules): number
	local caps = rules.caps
	return (caps and caps[itemId]) or rules.cap
end

local function isInput(itemId: string, rules: Rules): boolean
	for _, recipe in rules.recipes do
		if recipe.ins[itemId] then
			return true
		end
	end
	return false
end

-- How many of this item the machine can take right now.
function ProcessLogic.room(state: State, itemId: string, rules: Rules): number
	local wanted = isInput(itemId, rules) or (rules.usesFuel and rules.fuel[itemId] ~= nil)
	if not wanted then
		return 0
	end
	return math.max(0, capOf(itemId, rules) - (state.buf[itemId] or 0))
end

function ProcessLogic.insert(state: State, itemId: string, n: number, rules: Rules): number
	local taken = math.min(n, ProcessLogic.room(state, itemId, rules))
	if taken <= 0 then
		return 0
	end
	state.buf[itemId] = (state.buf[itemId] or 0) + taken
	return taken
end

local function waiting(state: State): number
	local total = 0
	for _, n in state.out do
		total += n
	end
	return total
end

-- The first recipe whose ingredients are all in the buffer.
local function ready(state: State, rules: Rules): Recipe?
	for _, recipe in rules.recipes do
		local ok = true
		for id, n in recipe.ins do
			if (state.buf[id] or 0) < n then
				ok = false
				break
			end
		end
		if ok then
			return recipe
		end
	end
	return nil
end

local function take(buf: { [string]: number }, id: string, n: number)
	local left = (buf[id] or 0) - n
	if left > 0 then
		buf[id] = left
	else
		buf[id] = nil
	end
end

-- The item to burn when the fuel has run out. The weakest fuel goes first, so a log is burned
-- before coal. An item that the waiting recipe needs is only burned if there is more of it than
-- the recipe uses.
local function fuelToBurn(state: State, rules: Rules, recipe: Recipe): string?
	local best: string? = nil
	for id, n in state.buf do
		local value = rules.fuel[id]
		if value and n > (recipe.ins[id] or 0) then
			if not best or value < rules.fuel[best] then
				best = id
			end
		end
	end
	return best
end

local function refuel(state: State, rules: Rules, recipe: Recipe)
	local best = fuelToBurn(state, rules, recipe)
	if best then
		take(state.buf, best, 1)
		state.fuel += rules.fuel[best]
	end
end

-- Is there a job the machine could start or carry on with? (Fuel aside: it is lit as work begins.)
function ProcessLogic.hasWork(state: State, rules: Rules): boolean
	return waiting(state) < rules.outCap and ready(state, rules) ~= nil
end

function ProcessLogic.isWorking(state: State, rules: Rules): boolean
	if waiting(state) >= rules.outCap or not ready(state, rules) then
		return false
	end
	return not rules.usesFuel or state.fuel > 0
end

function ProcessLogic.step(state: State, dt: number, rules: Rules)
	local guard = 0
	while guard < 64 do
		guard += 1
		local recipe = ready(state, rules)
		if not recipe or waiting(state) >= rules.outCap then
			state.progress = 0
			return
		end
		if rules.usesFuel and state.fuel <= 0 then
			refuel(state, rules, recipe)
			if state.fuel <= 0 then
				state.progress = 0
				return
			end
		end
		state.progress += dt
		dt = 0
		if state.progress < recipe.secs then
			return
		end
		state.progress -= recipe.secs
		for id, n in recipe.ins do
			take(state.buf, id, n)
		end
		for id, n in recipe.outs do
			state.out[id] = (state.out[id] or 0) + n
		end
		if rules.usesFuel then
			state.fuel = math.max(0, state.fuel - (rules.fuelPerJob or 1))
		end
	end
end

export type Flags = {
	halted: boolean?, -- stopped by a signal device
	needsPower: boolean?, -- cannot run without electricity
	powered: boolean?,
	stuck: boolean?, -- finished items have been unable to leave for a while
}

-- What the machine is doing, as a code (see shared/StatusText):
--   "halted"   stopped by a signal            "nopower"  needs electricity and has none
--   "blocked"  finished items cannot leave    "waiting"  no recipe has all its ingredients
--   "nofuel"   ready to work but nothing to burn          "working"  none of the above
function ProcessLogic.status(state: State, rules: Rules, flags: Flags): string
	if flags.halted then
		return "halted"
	end
	if flags.needsPower and not flags.powered then
		return "nopower"
	end
	if waiting(state) >= rules.outCap or (flags.stuck and next(state.out) ~= nil) then
		return "blocked"
	end
	local recipe = ready(state, rules)
	if not recipe then
		return "waiting"
	end
	if rules.usesFuel and state.fuel <= 0 and not fuelToBurn(state, rules, recipe) then
		return "nofuel"
	end
	return "working"
end

-- Everything a machine with these recipes takes in: ingredients, and fuel if it burns any.
function ProcessLogic.wanted(
	recipes: { Recipe },
	usesFuel: boolean,
	fuel: { [string]: number }
): { [string]: boolean }
	local wanted: { [string]: boolean } = {}
	for _, recipe in recipes do
		for id in recipe.ins do
			wanted[id] = true
		end
	end
	if usesFuel then
		for id in fuel do
			wanted[id] = true
		end
	end
	return wanted
end

local LIMIT = 2 ^ 31 -- a bag never holds this many of one thing

local function isAmount(n: any): boolean
	return type(n) == "number" and n == n and n % 1 == 0 and n >= 1 and n < LIMIT
end

-- A player puts something from their bag into the machine's ingredient slots by hand: as many as
-- were asked for, or as many as they have, or as many as fit, whichever is least. Returns how many
-- went in. What leaves the bag is exactly what enters the machine.
function ProcessLogic.deposit(
	state: State,
	bag: { [string]: number },
	itemId: any,
	n: any,
	rules: Rules
): number
	if type(itemId) ~= "string" or not isAmount(n) then
		return 0
	end
	local moved = math.min(n, bag[itemId] or 0, ProcessLogic.room(state, itemId, rules))
	if moved < 1 then
		return 0
	end
	take(bag, itemId, moved)
	state.buf[itemId] = (state.buf[itemId] or 0) + moved
	return moved
end

-- A player takes everything of one kind out of a slot ("buf" for ingredients, "out" for products)
-- into their bag. Returns how many came out.
function ProcessLogic.withdraw(state: State, bag: { [string]: number }, slot: any, itemId: any): number
	if type(itemId) ~= "string" or (slot ~= "buf" and slot ~= "out") then
		return 0
	end
	local pile = if slot == "buf" then state.buf else state.out
	local n = pile[itemId] or 0
	if n < 1 or (bag[itemId] or 0) + n >= LIMIT then
		return 0
	end
	take(pile, itemId, n)
	bag[itemId] = (bag[itemId] or 0) + n
	return n
end

-- A finished item that is waiting to leave, if there is one.
function ProcessLogic.peekOutput(state: State): string?
	return (next(state.out))
end

-- Removes one finished item of the given kind. Returns false if there was none.
function ProcessLogic.removeOutput(state: State, id: string): boolean
	if (state.out[id] or 0) < 1 then
		return false
	end
	take(state.out, id, 1)
	return true
end

-- Removes one finished item and says which it was.
function ProcessLogic.takeOutput(state: State): string?
	local id = ProcessLogic.peekOutput(state)
	if id then
		take(state.out, id, 1)
	end
	return id
end

local function cleanBag(
	raw: any,
	capFor: (string) -> number,
	isKnown: (string) -> boolean
): { [string]: number }
	local bag: { [string]: number } = {}
	if type(raw) == "table" then
		for id, n in raw do
			if type(id) == "string" and isKnown(id) and type(n) == "number" and n == n and n >= 1 then
				bag[id] = math.min(math.floor(n), capFor(id))
			end
		end
	end
	return bag
end

-- Rebuilds a state from stored data, dropping anything unknown and clamping the rest.
function ProcessLogic.sanitize(raw: any, rules: Rules, isKnown: (string) -> boolean): State
	local state = ProcessLogic.new()
	if type(raw) ~= "table" then
		return state
	end
	state.buf = cleanBag(raw.buf, function(id)
		return capOf(id, rules)
	end, isKnown)
	state.out = cleanBag(raw.out, function()
		return rules.outCap
	end, isKnown)
	if type(raw.fuel) == "number" and raw.fuel == raw.fuel then
		-- kept to the half, since a machine on electricity uses half a unit per job
		state.fuel = math.clamp(math.floor(raw.fuel * 2) / 2, 0, 64)
	end
	return state
end

return ProcessLogic
