-- A grid of tiles, each a picture with a name and a count, kept in step with a list of things.
-- Tiles are made once and reused: only the ones that come or go are built or destroyed, so a
-- count ticking up does not redraw every picture.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Defs = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Defs"))
local UIKit = require(script.Parent.UIKit)

local TileGrid = {}
TileGrid.__index = TileGrid

export type Entry = { key: string, count: number }

-- `grid` is a scroller laid out as a grid. `onClick` gets the key of the tile that was pressed.
-- `decorate`, if given, is called once for each new tile to add anything extra to it.
-- With `info` true, a right click or long press on a tile opens that thing's information card.
function TileGrid.new(
	grid: ScrollingFrame,
	width: number,
	height: number,
	onClick: (key: string) -> (),
	decorate: ((frame: Frame, key: string) -> ())?,
	info: boolean?
)
	return setmetatable({
		info = info == true,
		grid = grid,
		width = width,
		height = height,
		onClick = onClick,
		decorate = decorate,
		tiles = {} :: { [string]: Frame },
	}, TileGrid)
end

local function build(self, key: string): Frame
	local frame = UIKit.tile(self.grid, key, self.width, self.height, UIKit.Stock.name(key))
	local count = UIKit.label(frame, "", 12)
	count.Name = "Count"
	count.AnchorPoint = Vector2.new(1, 0)
	count.Position = UDim2.new(1, -5, 0, 3)
	count.Size = UDim2.fromOffset(60, 14)
	count.TextXAlignment = Enum.TextXAlignment.Right
	count.TextWrapped = false
	count.TextStrokeTransparency = 0.4
	count.ZIndex = 4
	UIKit.cover(frame, function()
		self.onClick(key)
	end, if self.info then key else nil)
	if self.decorate then
		self.decorate(frame, key)
	end
	return frame
end

-- Shows exactly the things in `list`, in that order.
function TileGrid.set(self, list: { Entry })
	local wanted = {}
	for order, entry in list do
		-- Things the game no longer knows cannot be drawn; skip them rather than fail.
		if UIKit.Stock.isKey(entry.key) or Defs.isEntry(entry.key) then
			wanted[entry.key] = true
			local frame = self.tiles[entry.key]
			if not frame then
				frame = build(self, entry.key)
				self.tiles[entry.key] = frame
			end
			frame.LayoutOrder = order
			local count = frame:FindFirstChild("Count") :: TextLabel
			count.Text = UIKit.number(entry.count)
		end
	end
	for key, frame in self.tiles do
		if not wanted[key] then
			frame:Destroy()
			self.tiles[key] = nil
		end
	end
end

return TileGrid
