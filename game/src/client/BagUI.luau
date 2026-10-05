-- The bag screen (B): everything the player holds. Pressing a thing puts it on the selected
-- hotbar slot, as something to place where it can be placed and as loose items otherwise.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared:WaitForChild("Defs"))
local ScreenLogic = require(Shared:WaitForChild("ScreenLogic"))
local Screens = require(script.Parent.Screens)
local TileGrid = require(script.Parent.TileGrid)
local UIKit = require(script.Parent.UIKit)

local BagUI = {}

local TILE_W, TILE_H = 92, 108

local hotbar
local tiles
local summary: TextLabel
local empty: TextLabel

local function put(entry: string)
	hotbar.assign(entry)
	UIKit.toast(Defs.name(entry) .. "을(를) " .. hotbar.selectedIndex() .. "번 칸에 넣었습니다")
end

local function onClick(key: string)
	local forms = ScreenLogic.forms(Defs, UIKit.Stock, key)
	local entry = forms.place or forms.drop
	if entry then
		put(entry)
	end
end

-- Things that are both a block and an item (a log, a stone) get a second, small button: the tile
-- itself puts them on the slot for building, this one for dropping on the ground or a belt.
local function decorate(frame: Frame, key: string)
	local forms = ScreenLogic.forms(Defs, UIKit.Stock, key)
	if forms.place and forms.drop then
		local drop = UIKit.button(frame, "던지기", 11)
		drop.Size = UDim2.fromOffset(44, 18)
		drop.Position = UDim2.fromOffset(4, 4)
		drop.BackgroundColor3 = UIKit.BACK
		drop.ZIndex = 6
		drop.Activated:Connect(function()
			put(forms.drop)
		end)
	end
end

local function refresh()
	local bag = hotbar.bag
	local kinds, total = ScreenLogic.totals(bag)
	summary.Text = if kinds > 0
		then kinds
			.. "종 · "
			.. UIKit.number(total)
			.. "개 · 누르면 지금 선택된 칸에 들어갑니다"
		else ""
	empty.Visible = kinds == 0
	tiles:set(ScreenLogic.sorted(Defs, UIKit.Stock, bag))
end

function BagUI.init(hotbarUi)
	hotbar = hotbarUi
	local _, body = UIKit.window("bag", "가방", 720, 470, Enum.KeyCode.B, refresh)

	summary = UIKit.label(body, "", 13)
	summary.TextColor3 = UIKit.DIM
	summary.TextXAlignment = Enum.TextXAlignment.Left
	summary.TextWrapped = false
	summary.Size = UDim2.new(1, 0, 0, 20)

	local grid = UIKit.scroller(body, Vector2.new(TILE_W, TILE_H), 8)
	grid.Position = UDim2.fromOffset(0, 28)
	grid.Size = UDim2.new(1, 0, 1, -28)
	tiles = TileGrid.new(grid, TILE_W, TILE_H, onClick, decorate)

	empty = UIKit.label(
		body,
		"가방이 비어 있습니다.\n생존 모드에서는 부순 것과 주운 것이 여기에 모입니다.",
		14
	)
	empty.TextColor3 = UIKit.DIM
	empty.Position = UDim2.fromOffset(0, 60)
	empty.Size = UDim2.new(1, 0, 0, 60)

	hotbar.onChange(function()
		if Screens.isOpen("bag") then
			refresh()
		end
	end)
end

return BagUI
