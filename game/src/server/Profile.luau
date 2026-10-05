-- What a player owns apart from the island itself: the bag, coins, workbench tiers and play mode.
-- This module tells the client when any of it changes and reads it back from stored data.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local CraftLogic = require(Shared.CraftLogic)
local Defs = require(Shared.Defs)
local Inventory = require(Shared.Inventory)
local Net = require(Shared.Net)
local Wallet = require(Shared.Wallet)
local ToolLogic = require(Shared.ToolLogic)
local Stock = require(Shared.Stock)(Defs)

local Profile = {}

Profile.Stock = Stock

function Profile.push(island)
	local player = island.owner
	Net.get("Bag"):FireClient(player, island.bag)
	Net.get("State"):FireClient(player, { mode = island.mode, coins = island.coins, tiers = island.tiers })
end

function Profile.notify(player: Player, text: string)
	Net.get("Notify"):FireClient(player, text)
end

local lastHint: { [Player]: number } = setmetatable({}, { __mode = "k" }) :: any

-- A notice that may be asked for many times a second (every swing) but is shown now and then.
function Profile.hint(player: Player, text: string)
	local now = os.clock()
	if now - (lastHint[player] or 0) > 2 then
		lastHint[player] = now
		Profile.notify(player, text)
	end
end

-- Records what the player says is in their hand. It is only a claim: inHand checks it.
function Profile.hold(island, entry: any)
	island.extra.held = if type(entry) == "string" and #entry <= 64 then Defs.itemOf(entry) else nil
end

-- A bag holding only the tool in the player's hand, for judging a swing. Empty if the hand holds
-- no tool or one the player does not have. In creative mode every tool is to hand.
function Profile.inHand(island): { [string]: number }
	return ToolLogic.inHand(island.bag, island.extra.held, island.mode == "creative")
end

Profile.NEED_TOOL = "곡괭이나 도끼 같은 도구를 손에 들어야 합니다"

-- Fills an island's owner data from what was stored, falling back to a fresh start for any part
-- that is missing or not valid.
function Profile.load(island, bag: any, stored: any)
	island.bag = Inventory.sanitize(bag, Stock.isKey)
	if type(stored) ~= "table" then
		return
	end
	island.coins = Wallet.sanitize(stored.coins, Config.START_COINS)
	island.tiers = CraftLogic.sanitizeTiers(stored.tiers)
	if stored.mode == "creative" or stored.mode == "survival" then
		island.mode = stored.mode
	end
	if type(stored.fuel) == "number" and stored.fuel == stored.fuel then
		island.handFuel = math.clamp(math.floor(stored.fuel), 0, 64)
	end
end

-- A player with no tool at all could do nothing, so they are handed the starting pickaxe again.
function Profile.ensureTool(island)
	if ToolLogic.count(island.bag) < 1 then
		Inventory.add(island.bag, "pick_wood", 1)
	end
end

function Profile.save(island): { [string]: any }
	return {
		mode = island.mode,
		coins = island.coins,
		tiers = table.clone(island.tiers),
		fuel = island.handFuel,
	}
end

return Profile
