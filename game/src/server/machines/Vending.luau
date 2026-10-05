-- The vending machine: how players sell to and buy from each other while the owner is busy.
-- The owner chooses one kind of thing, a price, and whether the machine sells it or buys it, and
-- stocks it from their bag. A visitor buys from it or sells to it, and the coins pass straight
-- between the two players. The rules live in shared/VendingLogic.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local Defs = require(Shared.Defs)
local Inventory = require(Shared.Inventory)
local ModelBuilder = require(Shared.ModelBuilder)
local VendingLogic = require(Shared.VendingLogic)
local IslandService = require(script.Parent.Parent.IslandService)
local Kit = require(script.Parent.Parent.MachineKit)
local MachineActs = require(script.Parent.Parent.MachineActs)
local Profile = require(script.Parent.Parent.Profile)
local StatusKit = require(script.Parent.Parent.StatusKit)

local Vending = {}

local Stock = Profile.Stock

local STATE_TEXT = {
	off = "꺼짐",
	empty = "재고 없음",
	nomoney = "돈 없음",
	full = "다 샀음",
	open = "영업 중",
}
local STATE_COLOUR = {
	off = { 150, 150, 150 },
	empty = { 230, 90, 80 },
	nomoney = { 230, 90, 80 },
	full = { 240, 190, 60 },
	open = { 120, 220, 140 },
}
local SHOW_SIZE = 1.3 -- studs: the thing on display is shrunk or grown to about this

-- Puts a small copy of what the machine deals in on top of it, so it can be seen from outside
-- what this machine is for.
local function showItem(machine)
	local item = machine.state.item
	if machine.shownItem == item then
		return
	end
	machine.shownItem = item
	if machine.display then
		machine.display:Destroy()
		machine.display = nil
	end
	if not item then
		return
	end
	local top = -Config.CELL / 2 + machine.def.height -- the machine's top, in its own frame
	local block = Stock.blockOf(item)
	if block then
		local def = Defs.Blocks[block]
		local cube = Kit.detail(
			machine.model,
			machine.base,
			Vector3.new(SHOW_SIZE, SHOW_SIZE, SHOW_SIZE) * 0.8,
			Vector3.new(0, top + SHOW_SIZE * 0.4, 0),
			Color3.fromRGB(def.color[1], def.color[2], def.color[3])
		)
		cube.Name = "Display"
		machine.display = cube
		return
	end
	local id = if Defs.Machines[item] then Defs.Machines[item].icon else "item_" .. item
	if not ModelBuilder.has(id) then
		return
	end
	local _, size = ModelBuilder.bounds(id)
	local scale = SHOW_SIZE / math.max(size.X, size.Y, size.Z)
	-- A model's own ground is half a cell below its base point; lift it so it stands on the top.
	local base = machine.base * CFrame.new(0, top + Config.CELL / 2 * scale, 0)
	local folder = ModelBuilder.build(machine.model, base, id, scale)
	if folder then
		folder.Name = "Display"
		machine.display = folder
	end
end

-- Writes on the outside of the machine what it sells or buys, the price, and whether it is open.
local function refresh(machine)
	local state = machine.state
	local code = VendingLogic.shopState(state, machine.island.coins)
	StatusKit.set(machine, code, STATE_COLOUR[code])
	showItem(machine)
	local text
	if code == "off" then
		text = "자판기\n" .. STATE_TEXT.off .. " · 물건과 값을 정해야 켜짐"
	elseif state.mode == "sell" then
		text = "팝니다: "
			.. Stock.name(state.item)
			.. "\n"
			.. state.price
			.. "코인 · 재고 "
			.. state.stock
			.. "\n"
			.. STATE_TEXT[code]
	else
		text = "삽니다: "
			.. Stock.name(state.item)
			.. "\n"
			.. state.price
			.. "코인 · "
			.. state.stock
			.. " / "
			.. state.limit
			.. "\n"
			.. STATE_TEXT[code]
	end
	StatusKit.say(machine, text)
end

-- What the machine's screen needs to draw itself for this player.
local function info(machine, player: Player)
	local state = machine.state
	local owner = machine.island
	return {
		item = state.item,
		price = state.price,
		mode = state.mode,
		stock = state.stock,
		limit = state.limit,
		isOwner = player == owner.owner,
		ownerName = owner.owner.DisplayName,
		-- in buy mode, how many more it will take right now
		wanted = VendingLogic.wanted(state, owner.coins),
	}
end

-- `setting` is true when the owner was changing the machine's settings.
local function explain(reason: string?, setting: boolean): string
	if reason == "item" then
		return "다룰 물건을 먼저 고르세요"
	elseif reason == "price" then
		return "가격은 1코인 이상이어야 합니다"
	elseif reason == "limit" and setting then
		return "살 개수는 1개 이상이어야 합니다"
	elseif reason == "unset" then
		return "먼저 물건과 가격을 정하세요"
	elseif reason == "closed" then
		return "지금은 거래할 수 없는 자판기입니다"
	elseif reason == "stock" then
		return "재고가 모자랍니다"
	elseif reason == "coins" then
		return "코인이 모자랍니다"
	elseif reason == "ownercoins" then
		return "주인의 코인이 모자랍니다"
	elseif reason == "limit" then
		return "자판기가 더 사지 않습니다"
	elseif reason == "missing" then
		return "그만큼 가지고 있지 않습니다"
	elseif reason == "full" then
		return "더 넣을 수 없습니다"
	end
	return "개수가 올바르지 않습니다"
end

function Vending.build(machine)
	Kit.visual(machine.model, machine.base, machine.id)
	local body = Kit.body(machine)
	machine.label = Kit.label(body, machine.def.height)
	machine.shown = ""
	-- This label is the shop's sign: bigger than a machine's read-out and readable from further off.
	local sign = machine.label.Parent
	if sign and sign:IsA("BillboardGui") then
		sign.Size = UDim2.fromOffset(260, 90)
		sign.MaxDistance = 70
		sign.StudsOffsetWorldSpace = Vector3.new(0, machine.def.height / 2 + 2.6, 0)
	end
	machine.label.TextSize = 16
	-- The lamp sits at a front corner, leaving the middle of the top for the thing on display.
	StatusKit.attach(machine, Vector3.new(1.1, 0, 1.1))
	machine.sinceLook = 0
	machine.state = VendingLogic.new()
	Kit.prompt(machine, body, "열기", function(player)
		MachineActs.show(player, machine, "vending", info(machine, player))
	end)
	refresh(machine)
end

function Vending.load(machine, saved)
	machine.state = VendingLogic.sanitize(saved, Stock.isKey)
	refresh(machine)
end

function Vending.save(machine)
	return table.clone(machine.state)
end

-- Whether a buying machine is open depends on its owner's coins, which change elsewhere, so the
-- sign is looked over once a second.
function Vending.tick(machine, dt: number)
	machine.sinceLook += dt
	if machine.sinceLook >= 1 then
		machine.sinceLook = 0
		refresh(machine)
	end
end

-- Reached through MachineActs, which has already checked the request's shape and the distance.
function Vending.act(machine, player: Player, action: string, arg: any)
	local state = machine.state
	local owner = machine.island
	local isOwner = player == owner.owner
	local ok, reason = false, nil

	if action == "configure" then
		if not isOwner or type(arg) ~= "table" then
			return
		end
		ok, reason =
			VendingLogic.configure(state, owner.bag, arg.item, arg.price, arg.mode, arg.limit, Stock.isKey)
		if ok then
			Profile.push(owner) -- old stock may have come back to the bag
		end
	elseif action == "deposit" or action == "withdraw" then
		if not isOwner then
			return
		end
		if action == "deposit" then
			ok, reason = VendingLogic.deposit(state, owner.bag, arg)
		else
			ok, reason = VendingLogic.withdraw(state, owner.bag, arg)
		end
		if ok then
			Profile.push(owner)
		end
	elseif action == "buy" or action == "sell" then
		-- The owner stocks and empties the machine; trading with it is for everyone else.
		local visitor = IslandService.get(player)
		if isOwner or not visitor then
			return
		end
		local item = state.item
		local visitorCoins, ownerCoins
		if action == "buy" then
			ok, reason, visitorCoins, ownerCoins =
				VendingLogic.purchase(state, visitor.bag, visitor.coins, owner.coins, arg)
		else
			ok, reason, visitorCoins, ownerCoins =
				VendingLogic.supply(state, visitor.bag, visitor.coins, owner.coins, arg)
		end
		if ok and item then
			local moved = math.abs(visitorCoins - visitor.coins)
			visitor.coins, owner.coins = visitorCoins, ownerCoins
			Profile.push(visitor)
			Profile.push(owner)
			local what = Stock.name(item) .. " " .. arg .. "개"
			if action == "buy" then
				Profile.notify(player, what .. "를 " .. moved .. "코인에 샀습니다")
				Profile.notify(
					owner.owner,
					player.DisplayName
						.. "님이 자판기에서 "
						.. what
						.. "를 샀습니다 (+"
						.. moved
						.. "코인)"
				)
			else
				Profile.notify(player, what .. "를 " .. moved .. "코인에 팔았습니다")
				Profile.notify(
					owner.owner,
					player.DisplayName
						.. "님이 자판기에 "
						.. what
						.. "를 팔았습니다 (-"
						.. moved
						.. "코인)"
				)
			end
		end
	else
		return
	end

	if not ok then
		Profile.notify(player, explain(reason, action == "configure"))
	end
	refresh(machine)
	MachineActs.show(player, machine, "vending", info(machine, player))
end

-- When the machine is broken its stock goes back into the owner's bag rather than onto the
-- ground: the stock may be machines or blocks, which cannot lie about as loose items.
function Vending.drops(machine): { [string]: number }
	local state = machine.state
	if state.item and state.stock > 0 and Inventory.add(machine.island.bag, state.item, state.stock) then
		state.stock = 0
		Profile.push(machine.island)
	end
	return {}
end

return Vending
