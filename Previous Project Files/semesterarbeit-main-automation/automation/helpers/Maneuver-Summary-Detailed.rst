stk.v.9.0

BEGIN ReportStyle
Name		Maneuver Summary Detailed

BEGIN ClassId
	Class		Satellite
END ClassId

BEGIN Header
	StyleType		0
	Date		Yes
	Name		Yes
	DescShort		No
	DescLong		No
	YLog10		No
	Y2Log10		No
	Ticks		No
	GridLines		No
	NumAnnotations		3
	AnnotationRotation		1
	NumTick		12
	NumGridX		12
	NumGridY		12
	BackgroundColor		#ffffff
	ViewableDuration		3600.000000
	RealTimeMode		No
	LegendStatus		1

BEGIN PostProcessor
	Destination	0
	Use	0
	Destination	1
	Use	0
	Destination	2
	Use	0
	Destination	3
	Use	0
END PostProcessor
	NumSections		1
END Header

BEGIN Section
	Name		Section 1
	ClassName		Satellite
	NameInTitle		No
	ExpandMethod		0
	PropMask		4
	ShowIntervals		No
	NumIntervals		0
	NumLines		1

BEGIN Line
	Name		Line 1
	NumElements		8

BEGIN Element
	Name		Maneuver Summary-Maneuver Number
	IsIndepVar		No
	Title		Maneuver Number
	NameInTitle		Yes
	Service		ManeuverSummary
	Element		Maneuver Number
	SumAllowedMask		0
	SummaryOnly		No
	DataType		1
	UnitType		6
	LineStyle		0
	LineWidth		0
	LineColor		#000000
	PointStyle		0
	PointSize		0
	PointColor		#000000
	FillPattern		0
	FillColor		#000000
	PropMask		0
	UseScenUnits		Yes
END Element

BEGIN Element
	Name		Maneuver Summary-Segment
	IsIndepVar		No
	Title		Segment
	NameInTitle		Yes
	Service		ManeuverSummary
	Element		Segment
	SumAllowedMask		0
	SummaryOnly		No
	DataType		2
	UnitType		6
	LineStyle		0
	LineWidth		0
	LineColor		#000000
	PointStyle		0
	PointSize		0
	PointColor		#000000
	FillPattern		0
	FillColor		#000000
	PropMask		0
	UseScenUnits		Yes
END Element

BEGIN Element
	Name		Maneuver Summary-Start Time
	IsIndepVar		No
	Title		Start Time
	NameInTitle		Yes
	Service		ManeuverSummary
	Element		Start Time
	SumAllowedMask		0
	SummaryOnly		No
	DataType		0
	UnitType		2
	LineStyle		0
	LineWidth		0
	LineColor		#000000
	PointStyle		0
	PointSize		0
	PointColor		#000000
	FillPattern		0
	FillColor		#000000
	PropMask		0
	UseScenUnits		Yes
END Element

BEGIN Element
	Name		Maneuver Summary-Stop Time
	IsIndepVar		No
	Title		Stop Time
	NameInTitle		Yes
	Service		ManeuverSummary
	Element		Stop Time
	SumAllowedMask		0
	SummaryOnly		No
	DataType		0
	UnitType		2
	LineStyle		0
	LineWidth		0
	LineColor		#000000
	PointStyle		0
	PointSize		0
	PointColor		#000000
	FillPattern		0
	FillColor		#000000
	PropMask		0
	UseScenUnits		Yes
END Element

BEGIN Element
	Name		Maneuver Summary-Duration
	IsIndepVar		No
	Title		Duration
	NameInTitle		Yes
	Service		ManeuverSummary
	Element		Duration
	Format		%.3f
	SumAllowedMask		31
	SummaryOnly		No
	SumRequestMask		8
	DataType		0
	UnitType		1
	LineStyle		0
	LineWidth		0
	LineColor		#000000
	PointStyle		0
	PointSize		0
	PointColor		#000000
	FillPattern		0
	FillColor		#000000
	PropMask		0
BEGIN Event
	UseEvent		No
	EventValue		0.000000
	Direction		Both
	CreateFile		No
END Event
	UseScenUnits		Yes
END Element

BEGIN Element
	Name		Maneuver Summary-Finite Burn Duration
	IsIndepVar		No
	Title		Est./Act. Finite Burn Duration
	NameInTitle		Yes
	Service		ManeuverSummary
	Element		Finite Burn Duration
	Format		%.3f
	SumAllowedMask		31
	SummaryOnly		No
	SumRequestMask		8
	DataType		0
	UnitType		1
	LineStyle		0
	LineWidth		0
	LineColor		#000000
	PointStyle		0
	PointSize		0
	PointColor		#000000
	FillPattern		0
	FillColor		#000000
	PropMask		0
BEGIN Event
	UseEvent		No
	EventValue		0.000000
	Direction		Both
	CreateFile		No
END Event
	UseScenUnits		Yes
END Element

BEGIN Element
	Name		Maneuver Summary-Delta V
	IsIndepVar		No
	Title		Delta V
	NameInTitle		Yes
	Service		ManeuverSummary
	Element		Delta V
	Format		%.10f
	SumAllowedMask		31
	SummaryOnly		No
	SumRequestMask		8
	DataType		0
	UnitType		33
	LineStyle		0
	LineWidth		0
	LineColor		#000000
	PointStyle		0
	PointSize		0
	PointColor		#000000
	FillPattern		0
	FillColor		#000000
	PropMask		0
BEGIN Event
	UseEvent		No
	EventValue		0.000000
	Direction		Both
	CreateFile		No
END Event
	UseScenUnits		Yes
END Element

BEGIN Element
	Name		Maneuver Summary-Fuel Used
	IsIndepVar		No
	Title		Fuel Used
	NameInTitle		Yes
	Service		ManeuverSummary
	Element		Fuel Used
	Format		%.3f
	SumAllowedMask		31
	SummaryOnly		No
	SumRequestMask		8
	DataType		0
	UnitType		8
	LineStyle		0
	LineWidth		0
	LineColor		#000000
	PointStyle		0
	PointSize		0
	PointColor		#000000
	FillPattern		0
	FillColor		#000000
	PropMask		0
BEGIN Event
	UseEvent		No
	EventValue		0.000000
	Direction		Both
	CreateFile		No
END Event
	UseScenUnits		Yes
END Element

BEGIN Element
	Name		Maneuver Summary-Thruster/Engine
	IsIndepVar		No
	Title		Thruster/Engine
	NameInTitle		Yes
	Service		ManeuverSummary
	Element		Thruster/Engine
	SumAllowedMask		0
	SummaryOnly		No
	DataType		2
	UnitType		6
	LineStyle		0
	LineWidth		0
	LineColor		#000000
	PointStyle		0
	PointSize		0
	PointColor		#000000
	FillPattern		0
	FillColor		#000000
	PropMask		0
	UseScenUnits		Yes
END Element
END Line
END Section
END ReportStyle

