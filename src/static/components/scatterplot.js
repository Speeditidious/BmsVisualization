class Scatterplot {
    margin = {
        top: 40, right: 90, bottom: 20, left: 40
    }

    axis_margin = {
        top: 10, right: 10, bottom: 10, left: 10
    }

    legend_margin = {
        top: 50, right: 40, bottom: 40, left: 70
    }

    constructor(svg, tooltip, data, width = 550, height = 300) {
        this.svg = svg;
        this.tooltip = tooltip;
        this.data = data;
        this.width = width;
        this.height = height;

        this.handlers = {};
        this.clicked = [];
    }

    initialize() {
        this.svg = d3.select(this.svg);
        this.tooltip = d3.select(this.tooltip);
        this.container = this.svg.append("g");
        this.xAxis = this.svg.append("g");
        this.yAxis = this.svg.append("g");
        this.legend = this.svg.append("g");

        this.xVar = 'x';
        this.yVar = 'y';
        this.colorVar = 'level';

        this.xScale = d3.scaleLinear();
        this.yScale = d3.scaleLinear();
        this.zScale = d3.scaleOrdinal().range(d3.schemeCategory10)

        this.svg
            .attr("width", this.width + this.margin.left + this.margin.right)
            .attr("height", this.height + this.margin.top + this.margin.bottom);

        this.container.attr("transform", `translate(${this.margin.left}, ${this.margin.top})`);

        this.brush = d3.brush()
            .extent([[0, 0], [this.width, this.height]])
            .on("start brush", (event) => {
                this.brushCircles(event);
            })

        this.allGroupedData = this.data.map(d => ({
                ...d,
                groupedColorVar: this.groupColorVar(d[this.colorVar])
            }));
        
        this.filteredData = this.data;

        this.starSymbol = d3.symbol().type(d3.symbolStar).size(100);

        this.clearColorMap = ['#EEEEEE', '#808080', '#00DB04', '#1C58FF', '#FF0000', '#87CEEB'];
        this.clearTextMap = {0: 'NO PLAY', 1: 'FAILED', 2: 'EASY', 3: 'NORMAL', 4: 'HARD', 5: 'FC'}
    }

    update(filteredData, uploadedData, useClearColor) {
        this.container.call(this.brush)

        this.filteredData = filteredData
        this.uploadedData = uploadedData
        this.combinedData = filteredData.concat(uploadedData)

        const filteredGroupedData = filteredData.map(d => ({
            ...d,
            groupedColorVar: this.groupColorVar(d[this.colorVar])
        }));

        const uploadedGroupedData = uploadedData.map(d => ({
            ...d,
            groupedColorVar: this.groupColorVar(d[this.colorVar])
        }));

        this.xScale.domain(d3.extent(this.combinedData, d => d[this.xVar])).range([0 + this.axis_margin.left, this.width - this.axis_margin.right]);
        this.yScale.domain(d3.extent(this.combinedData, d => d[this.yVar])).range([this.height - this.axis_margin.top, 0 + this.axis_margin.bottom]);
        this.zScale.domain([...new Set(this.allGroupedData.map(d => d.groupedColorVar))]);
        this.filteredDomain = [...new Set(filteredGroupedData.map(d => d.groupedColorVar))]

        this.circles = this.container.selectAll("circle")
            .data(filteredGroupedData)
            .join("circle")
            .on("mouseover", (e, d) => {
                this.tooltip.select(".tooltip-inner")
                    .html(`⑤${d['level']}<br />Title: ${d['title']}<br />Artist: ${d['artist']}`);

                Popper.createPopper(e.target, this.tooltip.node(), {
                    placement: 'top',
                    modifiers: [
                        {
                            name: 'arrow',
                            options: {
                                element: this.tooltip.select(".tooltip-arrow").node(),
                            },
                        },
                        {
                            name: 'offset',
                            options: {
                                offset: [0, 10],
                            },
                        },
                    ],
                });

                this.tooltip.style("display", "block");
            })
            .on("mouseout", (d) => {
                this.tooltip.style("display", "none");
            });
        
        this.circles
            .on("click", (e, d) => {
                this.clicked.push(d)
                d3.select(e.target).classed("brushed", !d3.select(e.target).classed("brushed"));
                this.handlers.brush(this.clicked);
            })
            .transition()
            .attr("cx", d => this.xScale(d[this.xVar]))
            .attr("cy", d => this.yScale(d[this.yVar]))
            .attr("fill", d => {
                if (useClearColor) {
                    return this.clearColorMap[+d['clear']];
                } else {
                    return this.zScale(d.groupedColorVar);
                }
            })
            .attr("r", 3);
        
        this.uploadedCircles = this.container.selectAll("path")
            .data(uploadedGroupedData)
            .join("path")
            .on("mouseover", (e, d) => {
                this.tooltip.select(".tooltip-inner")
                    .html(`⑤???<br />Title: ${d['title']}<br />Artist: ${d['artist']}`);

                Popper.createPopper(e.target, this.tooltip.node(), {
                    placement: 'top',
                    modifiers: [
                        {
                            name: 'arrow',
                            options: {
                                element: this.tooltip.select(".tooltip-arrow").node(),
                            },
                        },
                        {
                            name: 'offset',
                            options: {
                                offset: [0, 10],
                            },
                        },
                    ],
                });

                this.tooltip.style("display", "block");
            })
            .on("mouseout", (d) => {
                this.tooltip.style("display", "none");
            });
        
        this.uploadedCircles
            .transition()
            .attr("d", this.starSymbol)
            .attr("transform", d => `translate(${this.xScale(d[this.xVar])}, ${this.yScale(d[this.yVar])})`)
            .attr("fill", "black")

        this.container.call(this.brush);

        this.xAxis
            .transition()
            .attr("transform", `translate(${this.margin.left}, ${this.margin.top + this.height})`)
            .call(d3.axisBottom(this.xScale));

        this.yAxis
            .transition()
            .attr("transform", `translate(${this.margin.left}, ${this.margin.top})`)
            .call(d3.axisLeft(this.yScale));

        this.updateLegend(useClearColor);
    }

    updateLegend(useClearColor) {
        this.legend.selectAll(".legend").remove();

        let legendData;
        if (useClearColor) {
            legendData = this.clearColorMap.map((color, index) => {
                return {
                    color: color,
                    label: `${this.clearTextMap[index]}`
                };
            }).reverse();
        } else {
            legendData = this.zScale.domain().filter(d => this.filteredDomain.includes(d)).sort((a, b) => {
                if (a.includes('-')) a = a.split('-')[0];
                if (b.includes('-')) b = b.split('-')[0];
                return +a - +b;
            });
        }
        
        const legend = this.legend.selectAll(".legend")
            .data(legendData)
            .join("g")
            .attr("class", "legend")
            .attr("transform", (d, i) => `translate(0, ${i * 20})`);

        if (useClearColor) {
            legend.append("circle")
                .attr("cx", this.width + this.legend_margin.left - 20)
                .attr("cy", this.legend_margin.top)
                .attr("r", 5)
                .style("fill", d => d.color);

            legend.append("text")
                .attr("x", this.width + this.legend_margin.left + 10 - 20)
                .attr("y", this.legend_margin.top)
                .attr("dy", ".35em")
                .style("text-anchor", "start")
                .text(d => d.label);
        } else {
            legend.append("circle")
                .attr("cx", this.width + this.legend_margin.left)
                .attr("cy", this.legend_margin.top)
                .attr("r", 5)
                .style("fill", d => this.zScale(d));

            legend.append("text")
                .attr("x", this.width + this.legend_margin.left + 10)
                .attr("y", this.legend_margin.top)
                .attr("dy", ".35em")
                .style("text-anchor", "start")
                .text(d => d);
        }
    }

    groupColorVar(value) {
        if (value >= 1 && value <= 9) return "1-9";
        if (value >= 10 && value <= 11) return "10-11";
        if (value >= 12 && value <= 13) return "12-13";
        return value.toString();
    }

    isBrushed(d, selection) {
        let [[x0, y0], [x1, y1]] = selection;
        let x = this.xScale(d[this.xVar]);
        let y = this.yScale(d[this.yVar]);

        return x0 <= x && x <= x1 && y0 <= y && y <= y1;
    }

    brushCircles(event) {
        let selection = event.selection;

        this.circles.classed("brushed", d => this.isBrushed(d, selection));
        this.uploadedCircles.classed("brushed", d => this.isBrushed(d, selection));

        if (this.handlers.brush){
            this.clicked = this.filteredData.filter(d => this.isBrushed(d, selection));
            this.handlers.brush(this.clicked);
        }
            
    }

    on(eventType, handler) {
        this.handlers[eventType] = handler;
    }
}