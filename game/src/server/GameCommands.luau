-- Chat commands for trying the real game's rules before there are screens for them.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local Defs = require(Shared.Defs)
local Inventory = require(Shared.Inventory)
local Commands = require(script.Parent.Commands)
local CraftService = require(script.Parent.CraftService)
local IslandService = require(script.Parent.IslandService)
local Profile = require(script.Parent.Profile)
local TradeService = require(script.Parent.TradeService)

local GameCommands = {}

local Stock = Profile.Stock

-- Things can be named by id ("ingot_fe", "block:planks") or by their Korean name without spaces.
local byName: { [string]: string } = {}
local function learn(key: string)
	byName[string.gsub(Stock.name(key), "%s", "")] = key
end
for id in Defs.Blocks do
	learn("block:" .. id)
end
for id in Defs.Machines do
	learn(id)
end
for id in Defs.Items do
	learn(id)
end

local function keyOf(word: string?): string?
	if not word then
		return nil
	end
	if Stock.isKey(word) then
		return word
	end
	return byName[word]
end

local function amount(word: string?, fallback: number): number
	local n = tonumber(word)
	return if n then math.floor(n) else fallback
end

local function findPlayer(name: string?): Player?
	if not name then
		return nil
	end
	local lower = string.lower(name)
	for _, player in Players:GetPlayers() do
		if string.lower(player.Name) == lower or string.lower(player.DisplayName) == lower then
			return player
		end
	end
	return nil
end

function GameCommands.start()
	Commands.register("mode", function(player, args)
		local island = IslandService.get(player)
		local mode = args[1]
		if not island or not Config.ALLOW_MODE_SWITCH or (mode ~= "creative" and mode ~= "survival") then
			return
		end
		island.mode = mode
		Profile.push(island)
		Profile.notify(
			player,
			if mode == "survival"
				then "생존 모드: 가방에 있는 것만 놓을 수 있고, 부수면 가방으로 돌아옵니다"
				else "크리에이티브 모드: 무엇이든 무한히 놓을 수 있습니다"
		)
	end)

	-- Only in creative mode: puts anything straight into the bag.
	Commands.register("give", function(player, args)
		local island = IslandService.get(player)
		local key = keyOf(args[1])
		if not island or island.mode ~= "creative" then
			Profile.notify(player, "/give는 크리에이티브 모드에서만 됩니다")
			return
		end
		if key and Inventory.add(island.bag, key, amount(args[2], 1)) then
			Profile.push(island)
		else
			Profile.notify(player, "그런 것은 없습니다")
		end
	end)

	Commands.register("craft", function(player, args)
		local key = keyOf(args[1])
		local index = key and CraftService.findCraft(player, key)
		if index then
			CraftService.craft(player, index, amount(args[2], 1))
		else
			Profile.notify(player, "만드는 법이 없습니다")
		end
	end)

	Commands.register("hand", function(player, args)
		local key = keyOf(args[1])
		local index = key and CraftService.findHand(player, key)
		if index then
			CraftService.hand(player, index, amount(args[2], 1))
		else
			Profile.notify(player, "손으로 만드는 법이 없습니다")
		end
	end)

	-- Takes a workbench by name ("기본작업대", "wb_basic") or by its kind ("basic").
	Commands.register("upgrade", function(player, args)
		local key = keyOf(args[1])
		local def = key and Defs.Machines[key]
		CraftService.upgrade(player, if def and def.bench then def.bench else args[1])
	end)

	Commands.register("can", function(player)
		local names = CraftService.available(player)
		Profile.notify(
			player,
			if #names > 0
				then "지금 만들 수 있는 것: " .. table.concat(names, ", ")
				else "지금 만들 수 있는 것이 없습니다"
		)
	end)

	Commands.register("trade", function(player, args)
		local target = findPlayer(args[1])
		if target then
			TradeService.ask(player, target)
		else
			Profile.notify(player, "그런 플레이어가 없습니다")
		end
	end)
	Commands.register("offer", function(player, args)
		local key = keyOf(args[1])
		if key then
			TradeService.offer(player, key, amount(args[2], 1))
		else
			Profile.notify(player, "그런 것은 없습니다")
		end
	end)
	Commands.register("coins", function(player, args)
		TradeService.coins(player, amount(args[1], 0))
	end)
	Commands.register("ready", function(player)
		TradeService.ready(player, true)
	end)
	Commands.register("unready", function(player)
		TradeService.ready(player, false)
	end)
	Commands.register("cancel", function(player)
		TradeService.cancel(player)
	end)
end

return GameCommands
