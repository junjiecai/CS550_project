import React from 'react';
import logo from './logo.svg';
import {useState, useEffect} from "react";
import './App.css';
import {Button, Space} from 'antd';
import {Typography} from "antd";
import {Row, Col, Card} from "antd"

function Simulator() {
    const [pixelData, setPixelData] = React.useState([])

    const update = () => {
        fetch("http://localhost:8000/central/step_over").then(response => {
            return response.json()
        }).then(data => {
            let pixelData = data['data']
            console.log(pixelData)

            const maxRows = 600
            const maxColumns = 600

            const rgbMapping: any = {
                "BG": [0, 0, 0],
                "A": [255, 0, 0],
                "B": [0, 255, 0],
            }

            const pixelSize = 1

            const canvas = document.getElementById('rasterCanvas') as HTMLCanvasElement
            const ctx = canvas.getContext('2d') as CanvasRenderingContext2D;
            for (let row = 0; row < maxRows; ++row) {
                for (let column = 0; column < maxColumns; ++column) {
                    let type = pixelData[row][column].cell_type
                    let rgb = rgbMapping[type]

                    ctx.fillStyle = 'rgb(' + rgb[0] + ',' + rgb[1] +
                        ',' + rgb[2] + ')';
                    ctx.fillRect(column,
                        row,
                        pixelSize,
                        pixelSize);
                }
            }
        })
    }

    useEffect(() => {
            update()
        }, []
    )

    return <div>
        <canvas id="rasterCanvas" width={600} height={600} style={{border: "1px solid black"}}></canvas>
        <Button onClick={(e: any) => update()}>Click</Button>
    </div>
}


function App() {
    return (
        <div className="App">
            <Card>
                <Typography>CS550 Project</Typography>
                <Typography>Junjie Cai</Typography>
            </Card>
            <Card>
                <Simulator></Simulator>
            </Card>
        </div>
    );
}

export default App;
