function isCompoundInterestJson(isCompound,isSimple,isCompoundJson=false) {
    let compoundInterestJsonContainer=document.getElementById("compoundInterestJsonContainer");
    let simpleInterestContainer=document.getElementById("simpleInterestContainer");

    let simpleInterestFields = document.querySelectorAll(".simpleInterestField");
    let compoundInterestFields = document.querySelectorAll(".compoundInterestField");

    if (isCompound){
        if (compoundInterestJsonContainer != null) {
            compoundInterestJsonContainer.style.display="block";
        }
        compoundInterestFields.forEach(field => {field.required=true;});
        let compoundInterestContainer=document.getElementById("compoundInterestContainer");
        let compoundInterestRangeContainer=document.getElementsByClassName("compoundInterestRange")[0];
        if (isCompoundJson){
            compoundInterestRangeContainer.style.display="flex";
            compoundInterestContainer.style.display="none";
        }
        else{
            compoundInterestRangeContainer.style.display="none";
            compoundInterestContainer.style.display="flex";
        }
    }
    else{
        if (compoundInterestJsonContainer != null) {
            compoundInterestJsonContainer.style.display="none";
        }
        compoundInterestFields.forEach(field => {field.required=false;});
    }
    if (isSimple) {
        if (simpleInterestContainer != null) {
            simpleInterestContainer.style.display="block";
        }
        simpleInterestFields.forEach(field => {field.required=true;});
    }
    else{
        if (simpleInterestContainer != null) {
            simpleInterestContainer.style.display="none";
        }
        simpleInterestFields.forEach(field => {field.required=false;});
    }
}

function isCompoundInterest(isCompound) {
    let compoundInterestFields=document.querySelectorAll(".compoundInterestRange")
    compoundInterestFields.forEach(field => {field.style.display = isCompound ? "none" : "flex";});
    
    document.getElementById("simpleInterestContainer").style.display = isCompound ? "none" : "none";
    document.getElementById("compoundInterestContainer").style.display = isCompound ? "flex" : "none";
}

function isSip(isSipInvestment) {
    let sipFields = document.querySelectorAll(".sipInfoField");
    let oneTimeInvestmentsFields = document.querySelectorAll(".oteInfoField");

    if (isSipInvestment){
        sipFields.forEach(field => {field.required=true;});
        oneTimeInvestmentsFields.forEach(field => {field.required=false;});
    }
    else{
        oneTimeInvestmentsFields.forEach(field => {field.required=true;});
        sipFields.forEach(field => {field.required=false;});
    }

    document.getElementById("sipInvestmentContainer").style.display = isSipInvestment ? "block" : "none";
    document.getElementById("oneTimeInvestmentContainer").style.display = isSipInvestment ? "none" : "block";
}

function addCompoundInterestField() {
    compoundInterestJsonContainer = document.getElementById('compoundInterestJsonContainer');
    compoundInterestRange = document.createElement('div');
    compoundInterestRange.classList.add('compoundInterestRange')
    compoundInterestRange.innerHTML = `
        <input type="number" name = "startyears[]" step="1" min="0" class = "compoundInterestField" placeholder="Years">
        <input type="number" name = "startmonths[]" step="1" min="0" max="12" class = "compoundInterestField" placeholder="Months">
        <input type="number" name = "startdays[]" step="1" min="0" max="31" class = "compoundInterestField" placeholder="Days">
        <p class="commonString">TO</p>
        <input type="number" name = "endyears[]" step="1" min="0" class = "compoundInterestField" placeholder="Years">
        <input type="number" name = "endmonths[]" step="1" min="0" max="12" class = "compoundInterestField" placeholder="Months">
        <input type="number" name = "enddays[]" step="1" min="0" max="31" class = "compoundInterestField" placeholder="Days">
        <p class="commonString">:</p>
        <input type="number" name = "compoundInterestRate[]" step="0.01" min="0" class = "compoundInterestField" placeholder="%">
        <input type="button" id="addButton" onclick="addCompoundInterestField()" value="+">
        <input type="button" id="removeButton" onclick="removeCompoundInterestField(this)" value="-">
    `
    compoundInterestJsonContainer.appendChild(compoundInterestRange)
}

function addVestingField() {
    vestingRangesContainer = document.getElementById('vestingRanges');
    vestingRange = document.createElement('div');
    vestingRange.classList.add('vestingRange');
    vestingRange.innerHTML=`
        <label for = "vestingDate" class="calendarLabel" style="color: white;">Vesting Date</label><input type="date" name = "vestingDate[]" class="vestingInfoField"  id ="vestingDate" required>
        <p class="commonString" style="color: white;">:</p>
        <input type="number" name = "vestingUnits[]" step="1" min="1" class = "vestingUnitField vestingInfoField" placeholder="Units" required>
        <p class="commonString" style="color: white;">Units</p>
        <input type="button" id="addButton" onclick="addVestingField()" value="+">
        <input type="button" id="removeButton" onclick="removeVestingField(this)" value="-">
    `
    vestingRangesContainer.appendChild(vestingRange);
}

function removeCompoundInterestField(button) {
    if (document.querySelectorAll('.compoundInterestRange').length >1) {
        button.parentElement.remove()
    }
}

function removeVestingField(button) {
    if (document.querySelectorAll('.vestingRange').length >1) {
        button.parentElement.remove()
    }
}

function createPieChart(data,locator) {
    data=JSON.parse(data.replace(/&#39;/g, '"'))
    
    var pieChartData = new google.visualization.DataTable()
    pieChartData.addColumn('string','Name')
    pieChartData.addColumn('number','Amount')
    for (let i=0; i< data.length; i++) {
        pieChartData.addRow([data[i][0],data[i][1]])
    }

    var pieChartAttribute = {
        title: 'INVESTMENT DISTRIBUTION (₹)',
        width: 1800,
        height: 550,
        is3D: true,
        backgroundColor: 'transparent',
        legend: {
            position: 'right',
            textStyle: {
                color: 'black',
                fontSize: 20,
                bold: true
            }
        },
        titleTextStyle: {
            fontSize: 34,         
            bold: true,
            fontName:'Times New Roman'   
        },
        chartArea: {
            left: 150,
            top: 150,
            width: '70%',
            height: '70%'
        }
    };

    pieChart = new google.visualization.PieChart(document.getElementById(locator));
    pieChart.draw(pieChartData, pieChartAttribute);

}

function checkUpdateEnabled(checkbox,isCompound,isSimple) {
    elements=document.getElementsByClassName("submitButton")
    if (checkbox.checked) {
        isCompoundInterestJson(isCompound,isSimple);
        for (let i=0;i<elements.length;i++){
            elements[i].style.display="block"
        }
    }
    else {
        isCompoundInterestJson(false,false);
        for (let i=0;i<elements.length;i++){
            elements[i].style.display="none"
        }
    }
}

function checkVestingInfoAvailable(checkbox) {
    elements=document.querySelectorAll(".vestingInfoField")
    if (checkbox.checked) {
        document.getElementById("vestingRanges").style.display="flex";
        elements.forEach(field => {field.required=true;});
    }
    else {
        document.getElementById("vestingRanges").style.display="none";
        elements.forEach(field => {field.required=false;});
    }
}

function searchStock(period="yearly") {
    document.getElementById("stockInformation").style.display="block";

    let stockExchange=document.querySelector('input[name="stockExchange"]:checked')?.value;
    let stockName=document.getElementById("stockName").value; 

    setStockInfo(stockExchange,stockName,period);
}

function searchMutualFund(period="yearly") {
    document.getElementById("mutualFundInformation").style.display="block";

    let mutualFundName = document.getElementById('mutualFundName').value;
    let mutualFundId = document.getElementById('mutualFundId').value;
    setMutualFundInfo(mutualFundName,mutualFundId,period);
}

function createLineChart(locator,xAxis,yAxis,lineChartElement,timeUnit='year',timeStepSize=1,isStepped=false) {
    xLabel = xAxis["Label"]
    xData = xAxis["Data"]

    let dataset=[]
    for (let i=0;i<yAxis.length;i++){
        dataset.push({
            label:yAxis[i]["Label"],
            data:yAxis[i]["Data"],
            borderColor:yAxis[i]["Color"],
            fill:false,
            stepped:isStepped,
            pointRadius:0,
            borderWidth:1
        })
    }
    
    if (lineChartElement instanceof Chart) {
        lineChartElement.destroy();
    }
    chart = document.getElementById(locator).getContext("2d");
    lineChartElement = new Chart(chart,{
        type:"line",
        data:{
            labels:xData,
            datasets:dataset
        },
        options:{
            responsive:true,
            plugins:{
                legend:{
                    display: true,
                    labels:{
                        color:"black",
                        font:{
                            size:30
                        },
                        padding: 20,                 
                        boxWidth: 50,                
                        boxHeight: 22,               
                        usePointStyle: false  
                    }
                }
            },
            scales: {
                x:{
                    type:'time',
                    time:{
                        unit:timeUnit,
                        stepSize:timeStepSize
                    },
                    ticks:{
                        color:'blue'
                    },
                    title:{
                        display: true,
                        text : xLabel,
                        color: 'blue',
                        font: {
                            size : 30,
                            weight: 'bold'
                        }
                    }
                },
                y:{
                    ticks:{
                        color:'black'
                    }
                }
            }
        }
    });
    return lineChartElement;
}

function setStockInfo(stockExchange,stockName,period) {
    return fetch("/myinvestments/stocks/addInvestment/searchStockInfo",{
        method: "POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({"stockExchange":stockExchange,
            "stockName":stockName,
            "period":period
        }),
    }).then(response => {
        if (!response.ok){
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json()
    }).then(data => {
        let period_map={
            "daily":["day",1],
            "weekly":["day",7],
            "monthly":["month",1],
            "yearly":["month",3]
        }
        const openPrice = data.open;
        const closePrice = data.close;
        const volume = data.volume;
        const date = data.date;
        const volumeLabel=data.volumeLabel;
        const currency=data.currency;
        stockLineChart=createLineChart("stockLineChart",
            {"Label":"DATE","Data":date},
            [{"Label":"Open Price","Data":openPrice,"Color":"green"},
             {"Label":"Close Price","Data":closePrice,"Color":"red"},
             {"Label":volumeLabel,"Data":volume,"Color":"blue"}],
            stockLineChart,
            period_map[period][0],
            period_map[period][1]);
        document.getElementById("stockPrice").value=closePrice[closePrice.length -1];
        document.querySelectorAll(".currency").forEach(field => {field.innerHTML=currency;});
        return ["$","¥","€","£","C$"].includes(currency);
    }).catch(error =>{
        console.error("Fetch error:", error);
        return false;
    })
}

function setMutualFundInfo(mutualFundName,mutualFundId,period) {
    return fetch('/myinvestments/mutualfunds/addInvestment/searchMutualFundInfo', {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({
            "mutualFundName":mutualFundName,
            "mutualFundSchemeId":mutualFundId,
            "period":period
        })
    }).then(response => {
        if (!response.ok){
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json()
    }).then(data => {
        let period_map={
            "daily":["day",1],
            "weekly":["day",7],
            "monthly":["month",1],
            "yearly":["month",3]
        }
        const date = data.date;
        const price = data.price;
        mutualFundLineChart=createLineChart("mutualFundLineChart",
            {"Label":"Date","Data":date},
            [{"Label":"NAV","Data":price,"Color":"blue"}],
            mutualFundLineChart,
            period_map[period][0],
            period_map[period][1]
        );
        document.getElementById('mutualFundUnitPrice').value=price[price.length-1];
    }).catch(error =>{
        console.error("Fetch error:", error);
        return false;
    })
}

function createVestingChart(locator,date,units,vestingLineChart=null) {
    vestingLineChart=createLineChart(locator,
                {"Label":"DATE","Data":date},
                [{"Label":"Number of Units in the Account","Data":units}],
                vestingLineChart,
                'month',
                3,
                true);
    const today=new Date();
    vestingLineChart.data.datasets[0].segment={
        borderColor: ctx => {
            let vestingDate = new Date(ctx.p0.parsed.x);
            if (vestingDate < today){
                return 'green';
            }
            else {
                return 'yellow';
            }
        },
        borderWidth: 4,
        pointRadius: 4,
        pointBackgroundColor: 'red'
    }
    vestingLineChart.update();
    return vestingLineChart;
                
}

function markInvestmentAsInactive(checkbox,id,investmentType) {
    console.log(checkbox.value);
    console.log(id);
    console.log(checkbox.value=='on');
    if (checkbox.value=='on'){
        return fetch('/myinvestments/setInactive',{
            headers:{
                'Content-Type':'application/json'
            },
            method:"POST",
            body:JSON.stringify({
                "InvestmentId":id,
                "InvestmentType":investmentType
            })
        }).then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);    
                }
            return response.json();
            }
        ).then(response => {
            window.location.href=response.redirect;
        })
    }
}