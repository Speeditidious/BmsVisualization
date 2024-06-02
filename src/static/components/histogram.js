class Histogram {
    margin = {
        top: 60, right: 40, bottom: 40, left: 40
    }

    legend_margin = {
        top: 40, right: 40, bottom: 30, left: 40
    }

    constructor(svg, tooltip, data, width = 600, height = 300) {
        this.svg = svg;
        this.tooltip = tooltip;
        this.width = width;
        this.height = height;
        this.data = data
    }

    initialize() {
        this.svg = d3.select(this.svg);
        this.tooltip = d3.select(this.tooltip);
        this.container = this.svg.append("g");
        this.legend = this.svg.append("g");
        this.xAxis = this.svg.append("g");
        this.yAxis = this.svg.append("g");
        this.popperInstance = null;

        this.xScale = d3.scaleLinear();
        this.yScale = d3.scaleBand().padding(0.3);
        this.clearColorMap = ['#87CEEB', '#FF0000', '#1C58FF', '#00DB04', '#808080', '#EEEEEE'];
        this.clearTextMap = {0: 'NO PLAY', 1: 'FAILED', 2: 'EASY', 3: 'NORMAL', 4: 'HARD', 5: 'FULL COMBO'}

        this.svg
            .attr("width", this.width + this.margin.left + this.margin.right)
            .attr("height", this.height + this.margin.top + this.margin.bottom);

        this.container.attr("transform", `translate(${this.margin.left}, ${this.margin.top})`);
    }

    update(filteredData, yVar, stackVar) {
        this.yVar = yVar;
        this.stackVar = stackVar;
        
        const y_categories = [...new Set(filteredData.map(d => d[yVar]))];
        const stack_categories = [...new Set(this.data.map(d => d[stackVar]))];
        const legend_stack_categories = [...new Set(this.data.map(d => d[stackVar]))];

        const counts = {};
        const total_counts = {};

        y_categories.sort((a, b) => a - b);
        stack_categories.sort((a, b) => b - a);
        legend_stack_categories.sort((a, b) => b - a);

        y_categories.forEach(yc => {
            counts[yc] = {};
            stack_categories.forEach(sc => {
                counts[yc][sc] = filteredData.filter(d => d[yVar] === yc && d[stackVar] === sc).length;
            });
            total_counts[yc] = d3.sum(stack_categories.map(sc => counts[yc][sc]));
        });

        const color = d3.scaleOrdinal()
            .domain(stack_categories)
            .range(this.clearColorMap);

        const stack = d3.stack()
            .keys(stack_categories)
            .value((d, key) => d[1][key]);

        const series = stack(Object.entries(counts));

        let cumulativeWidth = 0;
        const legendData = legend_stack_categories.map(category => {
            const textWidth = this.getTextWidth(this.clearTextMap[category], "16px sans-serif");
            const itemWidth = textWidth + 24;
            cumulativeWidth += itemWidth + 10;
            return { category, itemWidth };
        });

        const legendXOffset = (this.width - cumulativeWidth) / 2;

        const legendItems = this.legend.selectAll(".legend-item")
            .data(legend_stack_categories)
            .join("g")
            .attr("class", "legend-item")
            .attr("transform", (d, i) => {
                const x = legendXOffset + legendData.slice(0, i).reduce((acc, curr) => acc + curr.itemWidth + 10, 0);
                return `translate(${x}, 0)`;
            });

        legendItems.append("rect")
            .attr("x", 0)
            .attr("y", 4)
            .attr("width", 20)
            .attr("height", 10)
            .attr("fill", d => color(d));

        legendItems.append("text")
            .attr("x", 24)
            .attr("y", 9)
            .attr("dy", "0.35em")
            .text(d => this.clearTextMap[d]);
        
        this.legend.attr("transform", `translate(${this.margin.left}, ${this.margin.top - this.legend_margin.bottom})`);
    
        this.xScale = d3.scaleLinear()
            .domain([0, 100])
            .range([0, this.width]);

        this.yScale = d3.scaleBand()
            .domain(y_categories)
            .range([0, this.height])
            .padding(0.2);
            
        const bars = this.container.selectAll("g.series")
            .data(series)
            .join("g")
            .attr("class", "series")
            .attr("fill", d => color(d.key));

        bars.selectAll("rect")
            .data(d => d.filter(fd => total_counts[+fd.data[0]] > 0))
            .join("rect")
            .on("mouseover", (e, d) => {
                const barId = d.data[0];
                const relatedRects = this.container.selectAll("rect")
                    .filter(r => r.data[0] === barId);
                relatedRects.attr("fill-opacity", 0.5);

                this.tooltip.select(".tooltip-inner")
                    .style("text-align", "left")
                    .html(`
                        <div style="display: flex; align-items: center;">
                            ⑤${d.data[0]}
                        </div>
                        <div style="display: flex; align-items: center;">
                            <span style="width: 10px; height: 10px; background-color: ${this.clearColorMap[0]}; margin-right: 5px;"></span>FULL COMBO: ${d.data[1][5]}
                        </div>
                        <div style="display: flex; align-items: center;">
                            <span style="width: 10px; height: 10px; background-color: ${this.clearColorMap[1]}; margin-right: 5px;"></span>HARD: ${d.data[1][4]}
                        </div>
                        <div style="display: flex; align-items: center;">
                            <span style="width: 10px; height: 10px; background-color: ${this.clearColorMap[2]}; margin-right: 5px;"></span>NORMAL: ${d.data[1][3]}
                        </div>
                        <div style="display: flex; align-items: center;">
                            <span style="width: 10px; height: 10px; background-color: ${this.clearColorMap[3]}; margin-right: 5px;"></span>EASY: ${d.data[1][2]}
                        </div>
                        <div style="display: flex; align-items: center;">
                            <span style="width: 10px; height: 10px; background-color: ${this.clearColorMap[4]}; margin-right: 5px;"></span>FAILED: ${d.data[1][1]}
                        </div>
                        <div style="display: flex; align-items: center;">
                            <span style="width: 10px; height: 10px; background-color: ${this.clearColorMap[5]}; margin-right: 5px;"></span>NO PLAY: ${d.data[1][0]}
                        </div>`);

                const centerX = e.clientX;
                const centerY = e.target.getBoundingClientRect().y;

                const virtualElement = {
                    getBoundingClientRect: () => ({
                        width: 0,
                        height: 0,
                        top: centerY,
                        left: centerX,
                        right: centerX,
                        bottom: centerY,
                    }),
                };

                this.popperInstance = Popper.createPopper(virtualElement, this.tooltip.node(), {
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

                this.tooltip.style("display", "block")
            })
            .on("mousemove", (e, d) => {
                if (this.popperInstance){
                    const centerX = e.clientX;
                    const centerY = e.target.getBoundingClientRect().y;

                    const virtualElement = {
                        getBoundingClientRect: () => ({
                            width: 0,
                            height: 0,
                            top: centerY,
                            left: centerX,
                            right: centerX,
                            bottom: centerY,
                        }),
                    };

                    this.popperInstance.state.elements.reference = virtualElement;
                    this.popperInstance.update();
                }
            })
            .on("mouseout", (e, d) => {
                const barId = d.data[0];
                const relatedRects = this.container.selectAll("rect")
                    .filter(r => r.data[0] === barId);
                relatedRects.attr("fill-opacity", 1);

                this.tooltip.style("display", "none");
                this.popperInstance = null;
            })
            .transition()
            .attr("x", d => this.xScale(d[0] / total_counts[+d.data[0]] * 100))
            .attr("y", d => this.yScale(+d.data[0]))
            .attr("width", d => this.xScale((d[1] / total_counts[+d.data[0]]) * 100) - this.xScale((d[0] / total_counts[+d.data[0]]) * 100))
            .attr("height", this.yScale.bandwidth());
    
        this.xAxis
            .attr("transform", `translate(${this.margin.left}, ${this.margin.top + this.height})`)
            .call(d3.axisBottom(this.xScale));

        this.yAxis
            .attr("transform", `translate(${this.margin.left}, ${this.margin.top})`)
            .call(d3.axisLeft(this.yScale));
    }

    getTextWidth(text, font) {
        const canvas = document.createElement("canvas");
        const context = canvas.getContext("2d");
        context.font = font;
        return context.measureText(text).width;
    }
}