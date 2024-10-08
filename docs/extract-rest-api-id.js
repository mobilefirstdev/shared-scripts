#!/usr/bin/env node
'use strict'
let stdin = process.stdin,
    stdout = process.stdout,
    inputChunks = []

const stage = process.argv[2]
const serviceName = process.argv[3]
if (typeof stage === 'undefined') {
    const msg = "[ERROR] mandatory parameter 'stage' is not present"
    console.error(msg)
    console.error(`usage: aws apigateway get-rest-apis --profile=m1dev --output json | ${process.argv[1]} <stage>`)
    console.error(`   eg: aws apigateway get-rest-apis --profile=m1dev --output json | ${process.argv[1]} dev`)
    throw new Error(msg)
}
if (typeof serviceName === 'undefined') {
    const msg = "[ERROR] mandatory parameter 'serviceName' is not present"
    console.error(msg)
    throw new Error(msg)
}
const targetRestApiName = stage + '-' + serviceName

stdin.resume()
stdin.setEncoding('utf8')

stdin.on('data', function (chunk) {
    inputChunks.push(chunk);
})

stdin.on('end', function () {
    let inputJSON = inputChunks.join('')
    let parsedData = JSON.parse(inputJSON)
    parsedData.items.forEach(function (curr) {
        if (curr.name === targetRestApiName) {
            stdout.write(curr.id)
            stdout.write('\n')
        }
    })
})