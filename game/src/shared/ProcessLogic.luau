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
	return math.max(0, rules.cap - (state.buf[itemId] or 0))
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

-- Burns one item from the buffer when the fuel has run out. The weakest fuel goes first, so a
-- log is burned before coal. An item that the waiting recipe needs is only burned if there is more
-- of it than the recipe uses.
local function refuel(state: State, rules: Rules, recipe: Recipe)
	local best: string? = nil
	for id, n in state.buf do
		local value = rules.fuel[id]
		if value and n > (recipe.ins[id] or 0) then
			if not best or value < rules.fuel[best] then
				best = id
			end
		end
	end
	if best then
		take(state.buf, best, 1)
		state.fuel += rules.fuel[best]
	end
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
			state.fuel -= 1
		end
	end
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

local function cleanBag(raw: any, cap: number, isKnown: (string) -> boolean): { [string]: number }
	local bag: { [string]: number } = {}
	if type(raw) == "table" then
		for id, n in raw do
			if type(id) == "string" and isKnown(id) and type(n) == "number" and n == n and n >= 1 then
				bag[id] = math.min(math.floor(n), cap)
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
	state.buf = cleanBag(raw.buf, rules.cap, isKnown)
	state.out = cleanBag(raw.out, rules.outCap, isKnown)
	if type(raw.fuel) == "number" and raw.fuel == raw.fuel then
		state.fuel = math.clamp(math.floor(raw.fuel), 0, 64)
	end
	return state
end

return ProcessLogic
