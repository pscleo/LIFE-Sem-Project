stk.v.11.0
WrittenBy    STK_v11.1.0

BEGIN ReportStyle

BEGIN ClassId
	Class		Satellite
END ClassId

BEGIN Header
	StyleType		0
	Date		Yes
	Name		Yes
	IsHidden		No
	DescShort		No
	DescLong		No
	YLog10		No
	Y2Log10		No
	YUseWholeNumbers		No
	Y2UseWholeNumbers		No
	VerticalGridLines		No
	HorizontalGridLines		No
	AnnotationType		Spaced
	NumAnnotations		3
	NumAngularAnnotations		5
	ShowYAnnotations		Yes
	AnnotationRotation		1
	BackgroundColor		#ffffff
	ForegroundColor		#000000
	ViewableDuration		3600.000000
	RealTimeMode		No
	DayLinesStatus		1
	LegendStatus		1
	LegendLocation		1

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
	PropMask		2
	ShowIntervals		No
	NumIntervals		0
	NumLines		1

BEGIN Line
	Name		Line 1
	NumElements		4

BEGIN Element
	Name		Body Axes Orientation-Body-wx
	IsIndepVar		No
	IndepVarName		Time
	Title		wx
	NameInTitle		Yes
	Service		BodyOrientation
	Type		Body
	Element		wx
	SumAllowedMask		1543
	SummaryOnly		No
	DataType		0
	UnitType		7
	LineStyle		0
	LineWidth		0
	PointStyle		0
	PointSize		0
	FillPattern		0
	LineColor		#000000
	FillColor		#000000
	PropMask		0
	UseScenUnits		Yes
END Element

BEGIN Element
	Name		Body Axes Orientation-Body-wy
	IsIndepVar		No
	IndepVarName		Time
	Title		wy
	NameInTitle		Yes
	Service		BodyOrientation
	Type		Body
	Element		wy
	SumAllowedMask		1543
	SummaryOnly		No
	DataType		0
	UnitType		7
	LineStyle		0
	LineWidth		0
	PointStyle		0
	PointSize		0
	FillPattern		0
	LineColor		#000000
	FillColor		#000000
	PropMask		0
	UseScenUnits		Yes
END Element

BEGIN Element
	Name		Body Axes Orientation-Body-wz
	IsIndepVar		No
	IndepVarName		Time
	Title		wz
	NameInTitle		Yes
	Service		BodyOrientation
	Type		Body
	Element		wz
	SumAllowedMask		1543
	SummaryOnly		No
	DataType		0
	UnitType		7
	LineStyle		0
	LineWidth		0
	PointStyle		0
	PointSize		0
	FillPattern		0
	LineColor		#000000
	FillColor		#000000
	PropMask		0
	UseScenUnits		Yes
END Element

BEGIN Element
	Name		Body Axes Orientation-Body-w mag
	IsIndepVar		No
	IndepVarName		Time
	Title		w mag
	NameInTitle		Yes
	Service		BodyOrientation
	Type		Body
	Element		w mag
	SumAllowedMask		1543
	SummaryOnly		No
	DataType		0
	UnitType		7
	LineStyle		0
	LineWidth		0
	PointStyle		0
	PointSize		0
	FillPattern		0
	LineColor		#000000
	FillColor		#000000
	PropMask		0
	UseScenUnits		Yes
END Element
END Line
END Section

BEGIN LineAnnotations
END LineAnnotations
END ReportStyle

