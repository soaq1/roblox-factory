-- Trades between two players on the same server. The rules live in shared/TradeLogic; this module
-- pairs players up, feeds their requests in, and moves the goods when both have agreed.
-- One player asks; the trade opens when the other asks back.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Net = require(Shared.Net)
local TradeLogic = require(Shared.TradeLogic)
local IslandService = require(script.Parent.IslandService)
local Profile = require(script.Parent.Profile)
local RateLimit = require(script.Parent.RateLimit)

local TradeService = {}

local Stock = Profile.Stock

type Open = { session: TradeLogic.Session, a: Player, b: Player }

local asked: { [Player]: Player } = {} -- who each player has asked
local open: { [Player]: Open } = {}

local function describe(side: TradeLogic.Side): string
	local parts = {}
	for key, n in side.offer do
		table.insert(parts, Stock.name(key) .. " " .. n)
	end
	table.sort(parts)
	if side.coins > 0 then
		table.insert(parts, side.coins .. "코인")
	end
	local text = if #parts > 0 then table.concat(parts, ", ") else "없음"
	return text .. (if side.ready then " (준비됨)" else "")
end

-- Shows both players where the trade stands.
local function show(trade: Open)
	local s = trade.session
	local snapshot = {
		a = { name = trade.a.Name, offer = s.a.offer, coins = s.a.coins, ready = s.a.ready },
		b = { name = trade.b.Name, offer = s.b.offer, coins = s.b.coins, ready = s.b.ready },
	}
	local text = trade.a.Name .. ": " .. describe(s.a) .. "\n" .. trade.b.Name .. ": " .. describe(s.b)
	for _, player in { trade.a, trade.b } do
		Net.get("Trade"):FireClient(player, snapshot)
		Profile.notify(player, text)
	end
end

local function close(trade: Open, message: string?)
	for _, player in { trade.a, trade.b } do
		if open[player] == trade then
			open[player] = nil
		end
		if player.Parent then
			Net.get("Trade"):FireClient(player, nil)
			if message then
				Profile.notify(player, message)
			end
		end
	end
end

local function whoIn(trade: Open, player: Player): string
	return if trade.a == player then "a" else "b"
end

local function finish(trade: Open)
	local islandA, islandB = IslandService.get(trade.a), IslandService.get(trade.b)
	if not islandA or not islandB then
		close(trade, "거래가 취소되었습니다")
		return
	end
	local ok, reason, coinsA, coinsB =
		TradeLogic.complete(trade.session, islandA.bag, islandA.coins, islandB.bag, islandB.coins)
	if ok then
		islandA.coins, islandB.coins = coinsA, coinsB
		Profile.push(islandA)
		Profile.push(islandB)
		close(trade, "거래가 끝났습니다")
	elseif reason == "full" then
		show(trade)
		Profile.notify(trade.a, "받는 쪽 가방이나 지갑이 넘칩니다")
		Profile.notify(trade.b, "받는 쪽 가방이나 지갑이 넘칩니다")
	else
		show(trade)
		Profile.notify(trade.a, "내놓은 것이 바뀌어 다시 확인이 필요합니다")
		Profile.notify(trade.b, "내놓은 것이 바뀌어 다시 확인이 필요합니다")
	end
end

function TradeService.ask(player: Player, target: any)
	if typeof(target) ~= "Instance" or not target:IsA("Player") or target == player then
		return
	end
	if not IslandService.get(player) or not IslandService.get(target) then
		return
	end
	if open[player] or open[target] then
		Profile.notify(player, "이미 거래 중입니다")
		return
	end
	if asked[target] == player then
		asked[target] = nil
		asked[player] = nil
		local trade: Open = { session = TradeLogic.new(), a = target, b = player }
		open[player] = trade
		open[target] = trade
		show(trade)
		return
	end
	asked[player] = target
	Profile.notify(player, target.Name .. "님에게 거래를 청했습니다")
	Profile.notify(
		target,
		player.Name .. "님이 거래를 청했습니다. 받으려면 /trade " .. player.Name
	)
end

function TradeService.offer(player: Player, key: any, n: any)
	local trade, island = open[player], IslandService.get(player)
	if not trade or not island or not Stock.isKey(key) then
		return
	end
	local ok, reason = TradeLogic.setOffer(trade.session, whoIn(trade, player), key, n, island.bag)
	if ok then
		show(trade)
	else
		Profile.notify(
			player,
			if reason == "missing"
				then "그만큼 가지고 있지 않습니다"
				else "올릴 수 없습니다"
		)
	end
end

function TradeService.coins(player: Player, n: any)
	local trade, island = open[player], IslandService.get(player)
	if not trade or not island then
		return
	end
	local ok, reason = TradeLogic.setCoins(trade.session, whoIn(trade, player), n, island.coins)
	if ok then
		show(trade)
	else
		Profile.notify(
			player,
			if reason == "missing" then "코인이 모자랍니다" else "올릴 수 없습니다"
		)
	end
end

function TradeService.ready(player: Player, ready: any)
	local trade = open[player]
	if not trade or not TradeLogic.setReady(trade.session, whoIn(trade, player), ready) then
		return
	end
	if TradeLogic.isAgreed(trade.session) then
		finish(trade)
	else
		show(trade)
	end
end

function TradeService.cancel(player: Player)
	asked[player] = nil
	local trade = open[player]
	if trade then
		close(trade, player.Name .. "님이 거래를 취소했습니다")
	end
end

function TradeService.start()
	local actions = {
		ask = TradeService.ask,
		offer = TradeService.offer,
		coins = TradeService.coins,
		ready = TradeService.ready,
		cancel = TradeService.cancel,
	}
	Net.get("TradeAct").OnServerEvent:Connect(function(player: Player, action: any, a: any, b: any)
		local run = type(action) == "string" and actions[action]
		if run and RateLimit.allow(player) then
			run(player, a, b)
		end
	end)
	Players.PlayerRemoving:Connect(function(player)
		for asker, target in asked do
			if asker == player or target == player then
				asked[asker] = nil
			end
		end
		local trade = open[player]
		if trade then
			close(trade, "상대가 나가서 거래가 취소되었습니다")
		end
	end)
end

return TradeService
