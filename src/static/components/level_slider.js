class LevelSlider {
    constructor(id, data, minLevel=1, maxLevel=20) {
        this.id = id
        this.data = data
        this.levelVar = 'level'
        this.minLevel = minLevel
        this.maxLevel = maxLevel
    }

    initialize() {
        this.slider = document.getElementById(this.id);
        this.filteredData = this.data;

        noUiSlider.create(this.slider, {
            start: [this.minLevel, this.maxLevel],
            step: 1,
            range: {
                'min': [this.minLevel],
                'max': [this.maxLevel]
            },
            connect: true,
            format: {
                to: function(value) {
                    return Math.round(value);
                },
                from: function(value) {
                    return Number(value);
                }
            },
            pips: {
                mode: 'steps',
                density: 10
            }
        });

        this.noUiSlider = this.slider.noUiSlider
    }

    filterDataByLevel(minLevel, maxLevel) {
        this.filteredData = this.data.filter(d => d[this.levelVar] >= minLevel && d[this.levelVar] <= maxLevel);
        return this.filteredData;
    }
}