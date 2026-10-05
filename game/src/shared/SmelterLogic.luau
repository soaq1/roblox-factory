--!strict
-- What a smelter decides, separate from how it looks. Coal becomes fuel, ore becomes ingots.
local SmelterLogic = {}

export type State = { fuel: number, ore: number, progress: number, out: number }
export type Rules = {
	smeltTime: number,
	fuelPerCoal: number,
	maxFuel: number,
	maxOre: number,
	maxOut: number,
}

function SmelterLogic.new(): State
	return { fuel = 0, ore = 0, progress = 0, out = 0 }
end

-- How many of this item the smelter can take right now.
function SmelterLogic.room(state: State, itemId: string, rules: Rules): number
	if itemId == "coal" then
		return math.max(0, math.floor((rules.maxFuel - state.fuel) / rules.fuelPerCoal))
	elseif itemId == "iron_ore" then
		return math.max(0, rules.maxOre - state.ore)
	end
	return 0
end

-- Puts up to n items in and returns how many were taken.
function SmelterLogic.insert(state: State, itemId: string, n: number, rules: Rules): number
	local taken = math.min(n, SmelterLogic.room(state, itemId, rules))
	if taken <= 0 then
		return 0
	end
	if itemId == "coal" then
		state.fuel += taken * rules.fuelPerCoal
	else
		state.ore += taken
	end
	return taken
end

function SmelterLogic.isWorking(state: State, rules: Rules): boolean
	return state.ore > 0 and state.fuel > 0 and state.out < rules.maxOut
end

-- Advances time. Finished ingots wait in state.out until taken.
function SmelterLogic.step(state: State, dt: number, rules: Rules)
	if not SmelterLogic.isWorking(state, rules) then
		return
	end
	state.progress += dt
	while state.progress >= rules.smeltTime and SmelterLogic.isWorking(state, rules) do
		state.progress -= rules.smeltTime
		state.ore -= 1
		state.fuel -= 1
		state.out += 1
	end
	if not SmelterLogic.isWorking(state, rules) then
		state.progress = 0
	end
end

function SmelterLogic.takeOutput(state: State, n: number): number
	local taken = math.min(n, state.out)
	state.out -= taken
	return taken
end

local function whole(n: any, max: number): number
	if type(n) ~= "number" or n ~= n then
		return 0
	end
	return math.clamp(math.floor(n), 0, max)
end

-- Rebuilds a state from stored data, clamping anything out of range.
function SmelterLogic.sanitize(raw: any, rules: Rules): State
	local state = SmelterLogic.new()
	if type(raw) ~= "table" then
		return state
	end
	state.fuel = whole(raw.fuel, rules.maxFuel)
	state.ore = whole(raw.ore, rules.maxOre)
	state.out = whole(raw.out, rules.maxOut)
	return state
end

return SmelterLogic
