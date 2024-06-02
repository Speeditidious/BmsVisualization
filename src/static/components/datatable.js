class DataTable {
    constructor(id, data) {
        this.id = id;
        this.data = data;
        this.sortColumn = 'level';
        this.sortOrder = 'asc';
        this.columns = ['level', 'title', 'clear', 'bad_and_poor', 'rank'];
        this.clearTextMap = {0: 'NO PLAY', 1: 'FAILED', 2: 'EASY', 3: 'NORMAL', 4: 'HARD', 5: 'FULL COMBO'}
        this.rankTextMap = {0: 'N', 1: 'F', 2: 'E', 3: 'D', 4: 'C', 5: 'B', 6: 'A', 7: 'AA', 8: 'AAA'}
        this.currentPage = 0;
        this.maxPage = Math.ceil(this.data.length / 10);
        this.rowsPerPage = 10;
        this.initSortHandlers();
        this.sortData();
        this.update(this.data);
        this.updateSortIcons();
        this.initPaginationHandlers();
    }

    update(data) {
        let table = d3.select(this.id);
        this.data = data;
        let pageData = this.paginatedData()

        let rows = table
            .selectAll("tr")
            .data(pageData)
            .join("tr");

        rows.selectAll("td")
            .data(d => this.columns.map(c => {
                if (c === 'bad_and_poor') {
                    return +d['bad'] + +d['poor'];
                } else if (c === 'clear') {
                    return this.clearTextMap[+d[c]];
                } else if (c === 'rank') {
                    return this.rankTextMap[+d[c]];
                } else {
                    return d[c];
                }
            }))
            .join("td")
            .attr("class", (d, i) => {
                if (this.columns[i] === 'title'){
                    return 'title-column';
                } else if (this.columns[i] === 'clear'){
                    return 'clear-column';
                } else if (this.columns[i] === 'rank'){
                    return 'rank-column';
                } else {
                    return 'normal-column';
                }
            })
            .text(d => d);
        
        this.updateCurrentPageDisplay();
    }

    updateCurrentPageDisplay() {
        d3.select('#pageDisplay').text(`${this.currentPage + 1}/${this.maxPage}`);
    }

    initSortHandlers() {
        d3.selectAll('.sortable').on('click', (event) => {
            const column = event.target.getAttribute('data-column');
            this.sortOrder = (this.sortColumn === column && this.sortOrder === 'asc') ? 'desc' : 'asc';
            this.sortColumn = column;
            this.sortData();
            this.update(this.data);
            this.updateSortIcons();
        });
    }

    paginatedData() {
        const start = this.currentPage * this.rowsPerPage;
        this.maxPage = Math.ceil(this.data.length / 10);
        return this.data.slice(start, start + this.rowsPerPage);
    }

    initPaginationHandlers() {
        d3.select('#prevPage').on('click', () => {
            if (this.currentPage > 0) {
                this.currentPage--;
                this.update(this.data);
            }
        });

        d3.select('#nextPage').on('click', () => {
            if ((this.currentPage + 1) * this.rowsPerPage < this.data.length) {
                this.currentPage++;
                this.update(this.data);
            }
        });
    }

    updateSortIcons() {
        d3.selectAll('.sortable').classed('asc', false).classed('desc', false);
        d3.select(`[data-column="${this.sortColumn}"]`).classed(this.sortOrder, true);
    }

    sortData() {
        this.data.sort((a, b) => {
            if (this.sortColumn === 'bad_and_poor'){
                const sumA = a['bad'] + a['poor'];
                const sumB = b['bad'] + b['poor'];
                if (sumA < sumB) return this.sortOrder === 'asc' ? -1 : 1;
                if (sumA > sumB) return this.sortOrder === 'asc' ? 1 : -1;
                return 0;
            } else{
                if (a[this.sortColumn] < b[this.sortColumn]) return this.sortOrder === 'asc' ? -1 : 1;
                if (a[this.sortColumn] > b[this.sortColumn]) return this.sortOrder === 'asc' ? 1 : -1;
                return 0;
            }
        });
        this.currentPage = 0;
    }
}