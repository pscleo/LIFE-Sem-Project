stk.v.10.0
WrittenBy    STK_v10.1.1

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
	NumElements		11

BEGIN Element
	Name		Time
	IsIndepVar		Yes
	IndepVarName		Time
	Title		Time
	NameInTitle		No
	Service		Quats
	Element		Time
	SumAllowedMask		0
	SummaryOnly		No
	DataType		0
	UnitType		2
	LineStyle		0
	LineWidth		0
	LineColor		#000000
	PointStyle		0
	PointSize		0
	FillPattern		0
	FillColor		#000000
	PropMask		0
	UseScenUnits		Yes
END Element

BEGIN Element
	Name		Attitude Quaternions-q1
	IsIndepVar		No
	IndepVarName		Time
	Title		q1
	NameInTitle		Yes
	Service		Quats
	Element		q1
	SumAllowedMask		0
	SummaryOnly		No
	DataType		0
	UnitType		6
	LineStyle		0
	LineWidth		0
	LineColor		#000000
	PointStyle		0
	PointSize		0
	FillPattern		0
	FillColor		#000000
	PropMask		0
	UseScenUnits		Yes
END Element

BEGIN Element
	Name		Attitude Quaternions-q2
	IsIndepVar		No
	IndepVarName		Time
	Title		q2
	NameInTitle		Yes
	Service		Quats
	Element		q2
	SumAllowedMask		0
	SummaryOnly		No
	DataType		0
	UnitType		6
	LineStyle		0
	LineWidth		0
	LineColor		#000000
	PointStyle		0
	PointSize		0
	FillPattern		0
	FillColor		#000000
	PropMask		0
	UseScenUnits		Yes
END Element

BEGIN Element
	Name		Attitude Quaternions-q3
	IsIndepVar		No
	IndepVarName		Time
	Title		q3
	NameInTitle		Yes
	Service		Quats
	Element		q3
	SumAllowedMask		0
	SummaryOnly		No
	DataType		0
	UnitType		6
	LineStyle		0
	LineWidth		0
	LineColor		#000000
	PointStyle		0
	PointSize		0
	FillPattern		0
	FillColor		#000000
	PropMask		0
	UseScenUnits		Yes
END Element

BEGIN Element
	Name		Attitude Quaternions-q4
	IsIndepVar		No
	IndepVarName		Time
	Title		q4
	NameInTitle		Yes
	Service		Quats
	Element		q4
	SumAllowedMask		0
	SummaryOnly		No
	DataType		0
	UnitType		6
	LineStyle		0
	LineWidth		0
	LineColor		#000000
	PointStyle		0
	PointSize		0
	FillPattern		0
	FillColor		#000000
	PropMask		0
	UseScenUnits		Yes
END Element

BEGIN Element
	Name		Attitude Quaternions-wx
	IsIndepVar		No
	IndepVarName		Time
	Title		wx
	NameInTitle		Yes
	Service		Quats
	Element		wx
	SumAllowedMask		0
	SummaryOnly		No
	DataType		0
	UnitType		7
	LineStyle		0
	LineWidth		0
	LineColor		#000000
	PointStyle		0
	PointSize		0
	FillPattern		0
	FillColor		#000000
	PropMask		0
	UseScenUnits		Yes
END Element

BEGIN Element
	Name		Attitude Quaternions-wy
	IsIndepVar		No
	IndepVarName		Time
	Title		wy
	NameInTitle		Yes
	Service		Quats
	Element		wy
	SumAllowedMask		0
	SummaryOnly		No
	DataType		0
	UnitType		7
	LineStyle		0
	LineWidth		0
	LineColor		#000000
	PointStyle		0
	PointSize		0
	FillPattern		0
	FillColor		#000000
	PropMask		0
	UseScenUnits		Yes
END Element

BEGIN Element
	Name		Attitude Quaternions-wz
	IsIndepVar		No
	IndepVarName		Time
	Title		wz
	NameInTitle		Yes
	Service		Quats
	Element		wz
	SumAllowedMask		0
	SummaryOnly		No
	DataType		0
	UnitType		7
	LineStyle		0
	LineWidth		0
	LineColor		#000000
	PointStyle		0
	PointSize		0
	FillPattern		0
	FillColor		#000000
	PropMask		0
	UseScenUnits		Yes
END Element

BEGIN Element
	Name		Euler Angles-Seq 321-A
	IsIndepVar		No
	IndepVarName		Time
	Title		A
	NameInTitle		Yes
	Service		Euler
	Type		Seq 321
	Element		A
	SumAllowedMask		1543
	SummaryOnly		No
	DataType		0
	UnitType		3
	LineStyle		0
	LineWidth		0
	LineColor		#000000
	PointStyle		0
	PointSize		0
	FillPattern		0
	FillColor		#000000
	PropMask		0
	UseScenUnits		No
BEGIN Units
		AngleUnit		Degrees
END Units
END Element

BEGIN Element
	Name		Euler Angles-Seq 321-B
	IsIndepVar		No
	IndepVarName		Time
	Title		B
	NameInTitle		Yes
	Service		Euler
	Type		Seq 321
	Element		B
	SumAllowedMask		1543
	SummaryOnly		No
	DataType		0
	UnitType		3
	LineStyle		0
	LineWidth		0
	LineColor		#000000
	PointStyle		0
	PointSize		0
	FillPattern		0
	FillColor		#000000
	PropMask		0
	UseScenUnits		No
BEGIN Units
		AngleUnit		Degrees
END Units
END Element

BEGIN Element
	Name		Euler Angles-Seq 321-C
	IsIndepVar		No
	IndepVarName		Time
	Title		C
	NameInTitle		Yes
	Service		Euler
	Type		Seq 321
	Element		C
	SumAllowedMask		1543
	SummaryOnly		No
	DataType		0
	UnitType		3
	LineStyle		0
	LineWidth		0
	LineColor		#000000
	PointStyle		0
	PointSize		0
	FillPattern		0
	FillColor		#000000
	PropMask		0
	UseScenUnits		No
BEGIN Units
		AngleUnit		Degrees
END Units
END Element
END Line
END Section

BEGIN LineAnnotations
END LineAnnotations
END ReportStyle

