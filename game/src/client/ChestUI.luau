-- A chest, opened the way one is in Minecraft: the player's bag on the left, the chest on the
-- right. Pressing a thing in the bag moves it into the chest; pressing a thing in the chest moves
-- it into the bag. The amount buttons choose how many go at a time.
--
-- The server opens the window (through "MachineInfo", kind "chest") when the owner presses F on a
-- chest or a storage unit, and keeps sending the contents while it stays open, so things a belt
-- brings in appear as they arrive. The server decides what actually moves.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared:WaitForChild("Defs"))
local Net = require(Shared:WaitForChild("Net"))
local StoreLogic = require(Shared:WaitForChild("StoreLogic"))
local Screens = require(script.Parent.Screens)
local UIKit = require(script.Parent.UIKit)

local ChestUI = {}

local WINDOW = "chest"
local TILE_W, TILE_H = 84, 92
local ALL = 2 ^ 30 -- "all of them": more than a pile ever holds, and still a whole number

type Target = { owner: number, x: number, y: number, z: number, id: string }

local hotbar
local target: Target? = nil
local contents: { [string]: number } = {}
local amount = ALL
local title: TextLabel
local bagTitle: TextLabel
local chestTitle: TextLabel
local bagGrid: ScrollingFrame
local chestGrid: ScrollingFrame
local amountButtons: { [number]: TextButton } = {}
local drawn: { [string]: string } = {}

local Stock = UIKit.Stock

local function act(action: string, arg: any)
	local at = target
	if at then
		Net.get("MachineAct"):FireServer(at.owner, at.x, at.y, at.z, action, arg)
	end
end

local function signature(pile: { [string]: number }): string
	local parts = {}
	for key, n in pile do
		table.insert(parts, key .. "=" .. n)
	end
	table.sort(parts)
	return table.concat(parts, ",")
end

local function sortedKeys(pile: { [string]: number }): { string }
	local keys = {}
	for key in pile do
		table.insert(keys, key)
	end
	table.sort(keys, function(a, b)
		local na, nb = Stock.name(a), Stock.name(b)
		if na ~= nb then
			return na < nb
		end
		return a < b
	end)
	return keys
end

-- One side of the window: a tile for each kind of thing, which moves it across when pressed.
local function drawPile(name: string, grid: ScrollingFrame, pile: { [string]: number }, action: string)
	local sig = signature(pile)
	if drawn[name] == sig then
		return
	end
	drawn[name] = sig
	UIKit.clear(grid)
	for order, key in sortedKeys(pile) do
		local tile = UIKit.tile(grid, key, TILE_W, TILE_H, Stock.name(key) .. " " .. UIKit.number(pile[key]))
		tile.LayoutOrder = order
		UIKit.cover(tile, function()
			act(action, { key = key, n = amount })
		end)
	end
end

local function draw()
	local at = target
	if not at then
		return
	end
	title.Text = Defs.name(at.id)
	local bagKinds, bagTotal = StoreLogic.totals(hotbar.bag)
	local chestKinds, chestTotal = StoreLogic.totals(contents)
	bagTitle.Text = "내 가방 · "
		.. bagKinds
		.. "종 "
		.. UIKit.number(bagTotal)
		.. "개 · 누르면 상자로"
	chestTitle.Text = "상자 · "
		.. chestKinds
		.. "종 "
		.. UIKit.number(chestTotal)
		.. "개 · 누르면 가방으로"
	drawPile("bag", bagGrid, hotbar.bag, "put")
	drawPile("chest", chestGrid, contents, "take")
end

local function chooseAmount(n: number)
	amount = n
	for value, button in amountButtons do
		button.BackgroundColor3 = if value == n then UIKit.LINE else UIKit.PANEL
	end
end

local function sameTarget(payload): boolean
	local at = target
	return at ~= nil
		and at.owner == payload.owner
		and at.x == payload.x
		and at.y == payload.y
		and at.z == payload.z
end

local function onInfo(payload: any)
	if type(payload) ~= "table" or payload.kind ~= "chest" or type(payload.info) ~= "table" then
		return
	end
	-- A stale update for a window the player has already closed must not open it again.
	if payload.info.update == true and not (Screens.isOpen(WINDOW) and sameTarget(payload)) then
		return
	end
	if not sameTarget(payload) then
		act("close", nil)
		drawn = {}
	end
	target = { owner = payload.owner, x = payload.x, y = payload.y, z = payload.z, id = payload.id }
	contents = if type(payload.info.contents) == "table" then payload.info.contents else {}
	draw()
	Screens.open(WINDOW)
end

function ChestUI.init(hotbarUi)
	hotbar = hotbarUi
	local frame, body = UIKit.window(WINDOW, "", 900, 540, nil, nil, function()
		act("close", nil)
		target = nil
		drawn = {}
	end)
	title = frame:FindFirstChild("Title") :: TextLabel

	-- How many go with one press.
	local label = UIKit.label(body, "한 번에", 13)
	label.TextColor3 = UIKit.DIM
	label.TextXAlignment = Enum.TextXAlignment.Left
	label.Size = UDim2.fromOffset(50, 28)
	local x = 54
	for _, entry in { { 1, "1개" }, { 10, "10개" }, { ALL, "전부" } } do
		local value = entry[1] :: number
		local button = UIKit.button(body, entry[2] :: string, 13)
		button.AutoButtonColor = false
		button.Size = UDim2.fromOffset(58, 28)
		button.Position = UDim2.fromOffset(x, 0)
		button.Activated:Connect(function()
			chooseAmount(value)
		end)
		amountButtons[value] = button
		x += 64
	end

	local takeAll = UIKit.button(body, "상자 비우기 (전부 가방으로)", 13)
	takeAll.AnchorPoint = Vector2.new(1, 0)
	takeAll.Position = UDim2.fromScale(1, 0)
	takeAll.Size = UDim2.fromOffset(210, 28)
	takeAll.Activated:Connect(function()
		act("takeall", nil)
	end)

	local function side(left: boolean): (TextLabel, ScrollingFrame)
		local heading = UIKit.label(body, "", 12)
		heading.TextColor3 = UIKit.DIM
		heading.TextXAlignment = Enum.TextXAlignment.Left
		heading.TextWrapped = false
		heading.TextTruncate = Enum.TextTruncate.AtEnd
		heading.Position = if left then UDim2.fromOffset(0, 38) else UDim2.new(0.5, 8, 0, 38)
		heading.Size = UDim2.new(0.5, -8, 0, 18)
		local grid = UIKit.scroller(body, Vector2.new(TILE_W, TILE_H), 8)
		grid.Position = if left then UDim2.fromOffset(0, 60) else UDim2.new(0.5, 8, 0, 60)
		grid.Size = UDim2.new(0.5, -8, 1, -60)
		return heading, grid
	end
	bagTitle, bagGrid = side(true)
	chestTitle, chestGrid = side(false)
	chooseAmount(ALL)

	Net.get("MachineInfo").OnClientEvent:Connect(onInfo)
	-- The bag changed (something crossed over): both sides are looked over again.
	hotbar.onChange(function()
		if Screens.isOpen(WINDOW) then
			draw()
		end
	end)
end

return ChestUI
