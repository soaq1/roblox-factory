-- Crafting, hand work and workbench upgrades. The rules live in shared/CraftLogic; this module
-- works out which benches the player is standing near, runs the request against their bag, and
-- reports what happened.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local CraftLogic = require(Shared.CraftLogic)
local Defs = require(Shared.Defs)
local Net = require(Shared.Net)
local Recipes = require(Shared.Recipes)
local IslandService = require(script.Parent.IslandService)
local MachineService = require(script.Parent.MachineService)
local Profile = require(script.Parent.Profile)
local RateLimit = require(script.Parent.RateLimit)

local CraftService = {}

local Stock = Profile.Stock

-- The name of each kind of bench, for messages.
local benchNames: { [string]: string } = { bag = "가방" }
for _, def in Defs.Machines do
	if def.behavior == "bench" then
		benchNames[def.bench] = def.name
	end
end

local function rootPosition(player: Player): Vector3?
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if root and root:IsA("BasePart") then
		return root.Position
	end
	return nil
end

-- Which benches on the player's own island are within reach, and at what tier.
function CraftService.benchesNear(player: Player, island): CraftLogic.Benches
	local benches: CraftLogic.Benches = {}
	local position = rootPosition(player)
	if not position then
		return benches
	end
	for _, machine in MachineService.onIsland(island) do
		if
			machine.def.behavior == "bench"
			and (machine.center - position).Magnitude <= Config.BENCH_RANGE
		then
			local kind = machine.def.bench
			benches[kind] = math.max(benches[kind] or 0, island.tiers[kind] or 1)
		end
	end
	return benches
end

local function explain(reason: string?, detail: any): string
	if reason == "bench" then
		return (benchNames[detail] or tostring(detail)) .. " 가까이에서만 할 수 있습니다"
	elseif reason == "tier" then
		return "작업대 " .. tostring(detail) .. "단계가 필요합니다"
	elseif reason == "missing" then
		return Stock.name(detail) .. "이(가) 모자랍니다"
	elseif reason == "tool" then
		return Stock.name(detail) .. "이(가) 있어야 합니다"
	elseif reason == "fuel" then
		return "땔감이 모자랍니다"
	elseif reason == "full" then
		return "가방에 더 넣을 수 없습니다"
	elseif reason == "max" then
		return "이미 가장 높은 단계입니다"
	elseif reason == "kind" then
		return "그런 작업대는 없습니다"
	end
	return "개수가 올바르지 않습니다"
end

local function isIndex(index: any, list: { any }): boolean
	return type(index) == "number" and index % 1 == 0 and index >= 1 and index <= #list
end

function CraftService.craft(player: Player, index: any, times: any)
	local island = IslandService.get(player)
	if not island or not isIndex(index, Recipes.craft) then
		return
	end
	local recipe = Recipes.craft[index]
	local ok, reason, detail =
		CraftLogic.craft(island.bag, recipe, CraftService.benchesNear(player, island), times)
	if ok then
		Profile.push(island)
		Profile.notify(
			player,
			Stock.name(recipe.out) .. " " .. recipe.n * times .. "개를 만들었습니다"
		)
	else
		Profile.notify(player, Stock.name(recipe.out) .. ": " .. explain(reason, detail))
	end
end

function CraftService.hand(player: Player, index: any, times: any)
	local island = IslandService.get(player)
	if not island or not isIndex(index, Recipes.hand) then
		return
	end
	local recipe = Recipes.hand[index]
	local benches = CraftService.benchesNear(player, island)
	local ok, reason, detail, fuel =
		CraftLogic.hand(island.bag, recipe, benches, times, Recipes.fuel, island.handFuel)
	island.handFuel = fuel
	if ok then
		local made = {}
		for key, n in recipe.outs do
			table.insert(made, Stock.name(key) .. " " .. n * times)
		end
		table.sort(made)
		Profile.push(island)
		Profile.notify(player, table.concat(made, ", ") .. "을(를) 만들었습니다")
	else
		Profile.notify(player, explain(reason, detail))
	end
end

function CraftService.upgrade(player: Player, kind: any)
	local island = IslandService.get(player)
	if not island then
		return
	end
	local benches = CraftService.benchesNear(player, island)
	local ok, reason, detail = CraftLogic.upgrade(island.bag, island.tiers, benches, kind, Recipes.upgrades)
	if ok then
		Profile.push(island)
		Profile.notify(
			player,
			benchNames[kind] .. "이(가) " .. island.tiers[kind] .. "단계가 되었습니다"
		)
	else
		Profile.notify(player, explain(reason, detail))
	end
end

-- The first recipe making `key` that can be made right now, else the first one making it at all.
function CraftService.findCraft(player: Player, key: string): number?
	local island = IslandService.get(player)
	if not island then
		return nil
	end
	local benches = CraftService.benchesNear(player, island)
	local first: number? = nil
	for index, recipe in Recipes.craft do
		if recipe.out == key then
			first = first or index
			if not CraftLogic.blocked(island.bag, recipe, benches, 1) then
				return index
			end
		end
	end
	return first
end

-- The same for hand work, trying each on a copy of the bag.
function CraftService.findHand(player: Player, key: string): number?
	local island = IslandService.get(player)
	if not island then
		return nil
	end
	local benches = CraftService.benchesNear(player, island)
	local first: number? = nil
	for index, recipe in Recipes.hand do
		if recipe.outs[key] then
			first = first or index
			if
				CraftLogic.hand(table.clone(island.bag), recipe, benches, 1, Recipes.fuel, island.handFuel)
			then
				return index
			end
		end
	end
	return first
end

-- Everything the player could craft once, right now, with what they hold and where they stand.
function CraftService.available(player: Player): { string }
	local island = IslandService.get(player)
	local names = {}
	if island then
		local benches = CraftService.benchesNear(player, island)
		local seen = {}
		for _, recipe in Recipes.craft do
			if not seen[recipe.out] and not CraftLogic.blocked(island.bag, recipe, benches, 1) then
				seen[recipe.out] = true
				table.insert(names, Stock.name(recipe.out))
			end
		end
	end
	table.sort(names)
	return names
end

function CraftService.start()
	local function guarded(run)
		return function(player: Player, ...)
			if RateLimit.allow(player) then
				run(player, ...)
			end
		end
	end
	Net.get("Craft").OnServerEvent:Connect(guarded(CraftService.craft))
	Net.get("Hand").OnServerEvent:Connect(guarded(CraftService.hand))
	Net.get("Upgrade").OnServerEvent:Connect(guarded(CraftService.upgrade))
end

return CraftService
