# Fastag Bank Server XML API Documentation

## Overview
This document describes the XML-based APIs used for communication between the Fastag system and the Acquirer Bank server. It includes request/response schemas, field definitions, and environment URLs for UAT and Production.

---

## Environments

| Environment | Endpoint URL (to be provided by bank) |
|-------------|---------------------------------------|
| UAT         | `TBD`                                 |
| Production  | `TBD`                                 |

---

## 1. SyncTime API

### Purpose
Synchronize the toll plaza system time with the Acquirer Bank host.

### Request (SyncTime)

```
POST <UAT/PROD URL>
Content-Type: application/xml

<etc:ReqSyncTime xmlns:etc="http://npci.org/etc/schema/">
  <Head ver="1.0" ts="YYYY-MM-DDThh:mm:ss" orgId="XXXX" msgId="..." />
  <Signature>...</Signature>
</etc:ReqSyncTime>
```

#### Field Definitions (Request)
| Field   | Description                                 | Type         | Format/Length                | Mandatory |
|---------|---------------------------------------------|--------------|------------------------------|-----------|
| ver     | API version (should be "1.0")              | Alphanumeric | "1.0"                        | Yes       |
| ts      | Request timestamp (ISO 8601)                | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| orgId   | Organization ID (assigned by acquirer)      | Alphanumeric | 4                            | Yes       |
| msgId   | Message identifier (unique per request)     | Alphanumeric | 1-35                         | Yes       |
| Signature | Digital signature (placeholder for now)    | -            | -                            | Yes       |

---

### Response (Success)
```
<etc:RespSyncTime xmlns:etc="http://npci.org/etc/schema/">
  <Head msgId="..." orgId="..." ts="..." ver="1.0"/>
  <Resp respCode="000" result="SUCCESS" ts="YYYY-MM-DDThh:mm:ss">
    <Time serverTime="YYYY-MM-DDThh:mm:ss"/>
  </Resp>
  <Signature>...</Signature>
</etc:RespSyncTime>
```

### Response (Failure)
```
<etc:RespSyncTime xmlns:etc="http://npci.org/etc/schema/">
  <Head msgId="..." orgId="..." ts="..." ver="1.0"/>
  <Resp respCode="104" result="FAILURE" ts="YYYY-MM-DDThh:mm:ss">
    <Time />
  </Resp>
  <Signature>...</Signature>
</etc:RespSyncTime>
```

#### Field Definitions (Response)
| Field      | Description                                 | Type         | Format/Length                | Mandatory |
|------------|---------------------------------------------|--------------|------------------------------|-----------|
| msgId      | Echoed from request                         | Alphanumeric | 1-35                         | Yes       |
| orgId      | Echoed from request                         | Alphanumeric | 4                            | Yes       |
| ts         | Echoed from request                         | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| ver        | Echoed from request                         | Alphanumeric | "1.0"                        | Yes       |
| respCode   | "000" for success, "104" for failure        | Numeric      | 3                            | Yes       |
| result     | "SUCCESS" or "FAILURE"                      | Enum         | -                            | Yes       |
| serverTime | Current server time (success only)          | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes (success) |
| Signature  | Digital signature (placeholder for now)     | -            | -                            | Yes       |

---

## 2. Toll Plaza Heart Beat API

### Purpose
Report the availability status of each lane of the plaza to the acquiring bank. Sent periodically by the toll plaza.

### Request (TollplazaHbeatReq)
```
POST <UAT/PROD URL>
Content-Type: application/xml

<etc:TollplazaHbeatReq xmlns:etc="http://npci.org/etc/schema/">
  <Head msgId="0000000000000AB1002" orgId="IRBL" ts="YYYY-MM-DDThh:mm:ss" ver="1.0" />
  <Txn id="0000000000000AB1002" note="" refId="" refUrl="" ts="YYYY-MM-DDThh:mm:ss" type="Hbt" orgTxnId="">
    <Meta>
      <Meta1 name="" value=""/>
      <Meta2 name="" value=""/>
    </Meta>
    <HbtMsg type="ALIVE" acquirerId=""/>
    <Plaza geoCode="11.00,11.00" id="1234" name="Test Plaza" subtype="State" type="Toll" address="" fromDistrict="" toDistrict="" agencyCode="">
      <Lane id="1234" direction="E" readerId="" Status="OPEN" Mode="Normal" laneType="Dedicated"/>
      <Lane id="5678" direction="W" readerId="" Status="CLOSE" Mode="Maintenance" laneType="Hybrid"/>
    </Plaza>
  </Txn>
  <Signature>...</Signature>
</etc:TollplazaHbeatReq>
```

#### Field Definitions (Request)
| Field         | Description                                 | Type         | Format/Length                | Mandatory |
|---------------|---------------------------------------------|--------------|------------------------------|-----------|
| msgId         | Message identifier (unique per request)     | Alphanumeric | 1-35                         | Yes       |
| orgId         | Organization ID (assigned by acquirer)      | Alphanumeric | 4                            | Yes       |
| ts            | Request timestamp (ISO 8601)                | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| ver           | API version (should be "1.0")              | Alphanumeric | "1.0"                        | Yes       |
| id (Txn)      | Unique transaction ID (UUID recommended)    | Alphanumeric | 1-22                         | Yes       |
| note          | Description of the transaction              | String       | 0-50                         | Optional  |
| refId         | External reference number                   | Alphanumeric | 0-35                         | Optional  |
| refUrl        | URL for the transaction                     | String       | 0-35                         | Optional  |
| type (Txn)    | Type of transaction (e.g., "Hbt")          | Enum         | 1-20                         | Yes       |
| orgTxnId      | Original transaction ID (for reversal)      | Alphanumeric | 1-36                         | Optional  |
| Meta          | MIS/analysis info (name/value pairs)        | -            | -                            | Optional  |
| HbtMsg        | Heartbeat message info                     | -            | -                            | Yes       |
| Plaza         | Plaza info                                 | -            | -                            | Yes       |
| Lane          | Lane info (multiple allowed)                | -            | -                            | Yes       |
| Signature     | Digital signature (placeholder for now)     | -            | -                            | Yes       |

---

### Response (Success)
```
<etc:TollplazaHbeatResp xmlns:etc="http://npci.org/etc/schema/">
  <Head ver="1.0" ts="YYYY-MM-DDThh:mm:ss" orgId="PATH" msgId="0000000000000AB1002"/>
  <Txn id="0000000000000AB1002" note="" refId="" refUrl="" ts="YYYY-MM-DDThh:mm:ss" type="Hbt" orgTxnId="">
    <Resp errCode="" result="SUCCESS" ts="YYYY-MM-DDThh:mm:ss"/>
  </Txn>
  <Signature>...</Signature>
</etc:TollplazaHbeatResp>
```

### Response (Failure)
```
<etc:TollplazaHbeatResp xmlns:etc="http://npci.org/etc/schema/">
  <Head ver="1.0" ts="YYYY-MM-DDThh:mm:ss" orgId="PATH" msgId="0000000000000AB1002"/>
  <Txn id="0000000000000AB1002" note="" refId="" refUrl="" ts="YYYY-MM-DDThh:mm:ss" type="Hbt" orgTxnId="">
    <Resp errCode="102" result="FAILURE" ts="YYYY-MM-DDThh:mm:ss"/>
  </Txn>
  <Signature>...</Signature>
</etc:TollplazaHbeatResp>
```

#### Field Definitions (Response)
| Field      | Description                                 | Type         | Format/Length                | Mandatory |
|------------|---------------------------------------------|--------------|------------------------------|-----------|
| msgId      | Echoed from request                         | Alphanumeric | 1-35                         | Yes       |
| orgId      | Echoed from request                         | Alphanumeric | 4                            | Yes       |
| ts         | Echoed from request                         | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| ver        | Echoed from request                         | Alphanumeric | "1.0"                        | Yes       |
| id (Txn)   | Echoed from request                         | Alphanumeric | 1-22                         | Yes       |
| note       | Echoed from request                         | String       | 0-50                         | Optional  |
| refId      | Echoed from request                         | Alphanumeric | 0-35                         | Optional  |
| refUrl     | Echoed from request                         | String       | 0-35                         | Optional  |
| type (Txn) | Echoed from request                         | Enum         | 1-20                         | Yes       |
| orgTxnId   | Echoed from request                         | Alphanumeric | 1-36                         | Optional  |
| errCode    | Error code (empty for success)              | Numeric      | 3                            | Yes       |
| result     | "SUCCESS" or "FAILURE"                      | Enum         | -                            | Yes       |
| Signature  | Digital signature (placeholder for now)     | -            | -                            | Yes       |

---

## 3. Check Transaction Status API

### Purpose
Check the status of one or more transactions from the Acquirer bank. Used before reconciliation for transactions that are in-process or have no response.

### Request (ReqChkTxn)
```
POST <UAT/PROD URL>
Content-Type: application/xml

<etc:ReqChkTxn xmlns:etc="http://npci.org/etc/schema/">
  <Head ver="1.0" ts="YYYY-MM-DDThh:mm:ss" orgId="IRBL" msgId="..."/>
  <Txn id="..." note="" refId="" refUrl="" ts="YYYY-MM-DDThh:mm:ss" type="ChkTxn" orgTxnId="">
    <TxnStatusReqList>
      <Status txnId="..." txnDate="YYYY-MM-DD" plazaId="..." laneId="..."/>
      <!-- More <Status> elements as needed -->
    </TxnStatusReqList>
  </Txn>
  <Signature>...</Signature>
</etc:ReqChkTxn>
```

#### Field Definitions (Request)
| Field         | Description                                 | Type         | Format/Length                | Mandatory |
|---------------|---------------------------------------------|--------------|------------------------------|-----------|
| ver           | API version (should be "1.0")              | Alphanumeric | "1.0"                        | Yes       |
| ts            | Request timestamp (ISO 8601)                | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| orgId         | Organization ID (assigned by acquirer)      | Alphanumeric | 4                            | Yes       |
| msgId         | Message identifier (unique per request)     | Alphanumeric | 1-35                         | Yes       |
| id (Txn)      | Unique transaction ID (UUID recommended)    | Alphanumeric | 1-22                         | Yes       |
| note          | Description of the transaction              | String       | 0-50                         | Optional  |
| refId         | External reference number                   | Alphanumeric | 0-35                         | Optional  |
| refUrl        | URL for the transaction                     | String       | 0-35                         | Optional  |
| ts (Txn)      | Transaction origination time                | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| type (Txn)    | Type of transaction ("ChkTxn")             | Enum         | 1-20                         | Yes       |
| orgTxnId      | Original transaction ID (for reversal)      | Alphanumeric | 1-36                         | Optional  |
| TxnStatusReqList | List of status requests                  | -            | -                            | Yes       |
| Status        | Transaction status request                  | -            | -                            | Yes       |
| txnId         | Transaction ID to check                     | Alphanumeric | 1-22                         | Yes       |
| txnDate       | Date of transaction (YYYY-MM-DD)            | ISODate      | 10 chars                     | Yes       |
| plazaId       | Plaza ID                                   | Alphanumeric | 1-6                          | Yes       |
| laneId        | Lane ID                                    | Alphanumeric | 1-3                          | Yes       |
| Signature     | Digital signature (placeholder for now)     | -            | -                            | Yes       |

---

### Response (Success)
```
<etc:RespChkTxn xmlns:etc="http://npci.org/etc/schema/">
  <Head ver="1.0" ts="YYYY-MM-DDThh:mm:ss" orgId="..." msgId="..."/>
  <Txn id="..." note="" refId="" refUrl="" ts="YYYY-MM-DDThh:mm:ss" type="ChkTxn" orgTxnId="">
    <Resp ts="YYYY-MM-DDThh:mm:ss" result="SUCCESS" respCode="000" totReqCnt="1" sucessReqCnt="1">
      <TxnStatusReqList>
        <Status txnId="..." txnDate="YYYY-MM-DD" plazaId="..." laneId="..." result="SUCCESS" errCode="" settleDate="YYYY-MM-DD">
          <TxnList txnStatus="SUCCESS" txnReaderTime="YYYY-MM-DD" txnType="CREDIT" txnReceivedTime="YYYY-MM-DD" FareType="FULL" VehicleClass="4" RegNumber="ABC123" errCode="" />
        </Status>
        <!-- More <Status> elements as needed -->
      </TxnStatusReqList>
    </Resp>
  </Txn>
  <Signature>...</Signature>
</etc:RespChkTxn>
```

### Response (Failure)
```
<etc:RespChkTxn xmlns:etc="http://npci.org/etc/schema/">
  <Head ver="1.0" ts="YYYY-MM-DDThh:mm:ss" orgId="..." msgId="..."/>
  <Txn id="..." note="" refId="" refUrl="" ts="YYYY-MM-DDThh:mm:ss" type="ChkTxn" orgTxnId="">
    <Resp ts="YYYY-MM-DDThh:mm:ss" result="FAILURE" respCode="102" totReqCnt="1" sucessReqCnt="0"/>
  </Txn>
  <Signature>...</Signature>
</etc:RespChkTxn>
```

#### Field Definitions (Response)
| Field         | Description                                 | Type         | Format/Length                | Mandatory |
|---------------|---------------------------------------------|--------------|------------------------------|-----------|
| ver           | API version (should be "1.0")              | Alphanumeric | "1.0"                        | Yes       |
| ts            | Response timestamp (ISO 8601)               | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| orgId         | Organization ID (echoed from request)       | Alphanumeric | 4                            | Yes       |
| msgId         | Message identifier (echoed from request)    | Alphanumeric | 1-35                         | Yes       |
| id (Txn)      | Transaction ID (echoed from request)        | Alphanumeric | 1-22                         | Yes       |
| note          | Description of the transaction              | String       | 0-50                         | Optional  |
| refId         | External reference number                   | Alphanumeric | 0-35                         | Optional  |
| refUrl        | URL for the transaction                     | String       | 0-35                         | Optional  |
| ts (Txn)      | Transaction origination time                | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| type (Txn)    | Type of transaction ("ChkTxn")             | Enum         | 1-20                         | Yes       |
| orgTxnId      | Original transaction ID (for reversal)      | Alphanumeric | 1-36                         | Optional  |
| Resp          | Response element                            | -            | -                            | Yes       |
| result        | "SUCCESS", "FAILURE", or "PARTIAL"          | Enum         | -                            | Yes       |
| respCode      | Response code                               | Numeric      | -                            | Yes       |
| totReqCnt     | Total number of requests                    | Numeric      | -                            | Yes       |
| sucessReqCnt  | Number of successful requests               | Numeric      | -                            | Yes       |
| TxnStatusReqList | List of status responses                 | -            | -                            | Yes       |
| Status        | Status of each transaction                  | -            | -                            | Yes       |
| txnId         | Transaction ID checked                      | Alphanumeric | 1-22                         | Yes       |
| txnDate       | Date of transaction (YYYY-MM-DD)            | ISODate      | 10 chars                     | Yes       |
| plazaId       | Plaza ID                                   | Alphanumeric | 1-6                          | Yes       |
| laneId        | Lane ID                                    | Alphanumeric | 1-3                          | Yes       |
| result (Status)| "SUCCESS" or "FAILURE"                    | Enum         | -                            | Yes       |
| errCode       | Error code (if any)                         | Numeric      | 3                            | Optional  |
| settleDate    | Settlement date (if any)                    | ISODate      | 10 chars                     | Optional  |
| TxnList       | List of transaction details                 | -            | -                            | Optional  |
| txnStatus     | Status of the transaction                   | Enum         | -                            | Yes       |
| txnReaderTime | Time tag was read                           | ISODate      | 10 chars                     | Yes       |
| txnType       | Type of the transaction                     | Enum         | 1-20                         | Yes       |
| txnReceivedTime| Time transaction happened                  | ISODate      | 10 chars                     | Yes       |
| FareType      | Fare type                                   | Enum         | -                            | Optional  |
| VehicleClass  | Vehicle class                               | Alphanumeric | 0-5                          | Optional  |
| RegNumber     | Vehicle registration number                 | Alphanumeric | 4-20                         | Optional  |
| errCode (TxnList)| Error code for transaction               | Numeric      | 3                            | Optional  |
| Signature     | Digital signature (placeholder for now)     | -            | -                            | Yes       |

---

## 4. Request Tag Details API

### Purpose
Fetch details of a vehicle that passed through the toll plaza by providing TID, vehicle registration number, or Tag ID.

### Request (ReqTagDetails)
```
POST <UAT/PROD URL>
Content-Type: application/xml

<etc:ReqTagDetails xmlns:etc="http://npci.org/etc/schema/">
  <Head ver="1.0" ts="YYYY-MM-DDThh:mm:ss" orgId="IRBL" msgId="..." />
  <Txn id="..." note="" refId="" refUrl="" ts="YYYY-MM-DDThh:mm:ss" type="FETCH" orgTxnId="">
    <Vehicle TID="" vehicleRegNo="" tagId="..." />
  </Txn>
  <Signature>...</Signature>
</etc:ReqTagDetails>
```

#### Field Definitions (Request)
| Field         | Description                                 | Type         | Format/Length                | Mandatory |
|---------------|---------------------------------------------|--------------|------------------------------|-----------|
| ver           | API version (should be "1.0")              | Alphanumeric | "1.0"                        | Yes       |
| ts            | Request timestamp (ISO 8601)                | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| orgId         | Organization ID (assigned by acquirer)      | Alphanumeric | 4                            | Yes       |
| msgId         | Message identifier (unique per request)     | Alphanumeric | 1-35                         | Yes       |
| id (Txn)      | Unique transaction ID (UUID recommended)    | Alphanumeric | 1-22                         | Yes       |
| note          | Description of the transaction              | String       | 0-50                         | Optional  |
| refId         | External reference number                   | Alphanumeric | 0-35                         | Optional  |
| refUrl        | URL for the transaction                     | String       | 0-35                         | Optional  |
| ts (Txn)      | Transaction origination time                | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| type (Txn)    | Type of transaction ("FETCH")              | Enum         | 1-20                         | Yes       |
| orgTxnId      | Original transaction ID (for reversal)      | Alphanumeric | 1-36                         | Optional  |
| Vehicle       | Vehicle info (at least one of TID, vehicleRegNo, tagId required) | - | - | Yes |
| TID           | Tag TID                                    | Hexadecimal  | 24-32                        | Conditional |
| vehicleRegNo  | Vehicle registration number                 | Alphanumeric | 4-20                         | Conditional |
| tagId         | Tag ID                                     | Hexadecimal  | 20-32                        | Conditional |
| Signature     | Digital signature (placeholder for now)     | -            | -                            | Yes       |

---

### Response (Success)
```
<etc:RespTagDetails xmlns:etc="http://npci.org/etc/schema/">
  <Head msgId="..." orgId="..." ts="YYYY-MM-DDThh:mm:ss" ver="1.0"/>
  <Txn id="..." note="" orgTxnId="" refId="" refUrl="" ts="YYYY-MM-DDThh:mm:ss" type="FETCH">
    <Resp respCode="000" result="SUCCESS" successReqCnt="1" totReqCnt="1" ts="YYYY-MM-DDThh:mm:ss">
      <Vehicle errCode="000">
        <VehicleDetails>
          <Detail name="TAGID" value="..."/>
          <Detail name="REGNUMBER" value="..."/>
          <Detail name="TID" value="..."/>
          <Detail name="VEHICLECLASS" value="..."/>
          <Detail name="TAGSTATUS" value="..."/>
          <Detail name="EXCCODE" value="..."/>
          <Detail name="COMVEHICLE" value="..."/>
        </VehicleDetails>
      </Vehicle>
    </Resp>
  </Txn>
  <Signature>...</Signature>
</etc:RespTagDetails>
```

### Response (Failure)
```
<etc:RespTagDetails xmlns:etc="http://npci.org/etc/schema/">
  <Head msgId="..." orgId="..." ts="YYYY-MM-DDThh:mm:ss" ver="1.0"/>
  <Txn id="..." note="" orgTxnId="" refId="" refUrl="" ts="YYYY-MM-DDThh:mm:ss" type="FETCH">
    <Resp respCode="103" result="FAILURE" successReqCnt="0" totReqCnt="1" ts="YYYY-MM-DDThh:mm:ss" />
  </Txn>
  <Signature>...</Signature>
</etc:RespTagDetails>
```

#### Field Definitions (Response)
| Field         | Description                                 | Type         | Format/Length                | Mandatory |
|---------------|---------------------------------------------|--------------|------------------------------|-----------|
| msgId         | Echoed from request                         | Alphanumeric | 1-35                         | Yes       |
| orgId         | Echoed from request                         | Alphanumeric | 4                            | Yes       |
| ts            | Response timestamp (ISO 8601)               | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| ver           | API version (should be "1.0")              | Alphanumeric | "1.0"                        | Yes       |
| id (Txn)      | Transaction ID (echoed from request)        | Alphanumeric | 1-22                         | Yes       |
| note          | Description of the transaction              | String       | 0-50                         | Optional  |
| orgTxnId      | Original transaction ID (for reversal)      | Alphanumeric | 1-36                         | Optional  |
| refId         | External reference number                   | Alphanumeric | 0-35                         | Optional  |
| refUrl        | URL for the transaction                     | String       | 0-35                         | Optional  |
| ts (Txn)      | Transaction origination time                | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| type (Txn)    | Type of transaction ("FETCH")              | Enum         | 1-20                         | Yes       |
| Resp          | Response element                            | -            | -                            | Yes       |
| respCode      | Response code                               | Numeric      | 3                            | Yes       |
| result        | "SUCCESS" or "FAILURE"                      | Enum         | -                            | Yes       |
| successReqCnt | Number of successful requests               | Numeric      | 1-2                          | Yes       |
| totReqCnt     | Total number of requests                    | Numeric      | 1-2                          | Yes       |
| ts (Resp)     | Response timestamp (ISO 8601)               | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| Vehicle       | Vehicle info                               | -            | -                            | Conditional |
| errCode       | Error code (if any)                         | Numeric      | 3                            | Optional  |
| VehicleDetails| List of vehicle details                     | -            | -                            | Optional  |
| Detail        | Name/value pairs for vehicle info           | -            | -                            | Optional  |
| Signature     | Digital signature (placeholder for now)     | -            | -                            | Yes       |

---

## 5. Request Pay API

### Purpose
Initiate a debit or credit transaction for a vehicle passing through the toll plaza. The request is sent to the Acquirer bank, which processes it and responds asynchronously.

### Request (ReqPay)
```
POST <UAT/PROD URL>
Content-Type: application/xml

<etc:ReqPay xmlns:etc="http://npci.org/etc/schema/">
  <Head msgId="..." orgId="IRBL" ts="YYYY-MM-DDThh:mm:ss" ver="1.0" />
  <Meta>
    <!-- Optional: <Tag name="..." value="..."/> -->
  </Meta>
  <Txn id="..." note="" orgTxnId="" refId="" refUrl="" ts="YYYY-MM-DDThh:mm:ss" type="DEBIT" >
    <EntryTxn id="..." tsRead="YYYY-MM-DDThh:mm:ss" type="DEBIT" />
  </Txn>
  <Plaza geoCode="11.00,11.00" id="1234" name="Test Plaza" subtype="State" type="Toll">
    <EntryPlaza geoCode="11.00,11.00" id="1234" name="Test Plaza" subtype="State" type="Toll" />
    <Lane direction="N" id="a" readerId="12" Status="OPEN" laneType="Dedicated" ExitGate="" Floor="" Mode="Normal" />
    <EntryLane direction="N" id="a" readerId="12" Status="OPEN" Mode="Normal" laneType="Dedicated" EntryGate="" Floor="" />
    <ReaderVerificationResult publicKeyCVV="" procRestrictionResult="" tagVerified="NETC TAG" ts="YYYY-MM-DDThh:mm:ss" txnCounter="1234" vehicleAuth="UNKNOWN" >
      <TagUserMemory>
        <Detail name="TagSignature" value="" />
        <Detail name="TagVRN" value="XXXXXXXXXXXX" />
        <Detail name="TagVC" value="04" />
      </TagUserMemory>
    </ReaderVerificationResult>
  </Plaza>
  <Vehicle TID="..." tagId="..." wim="" staticweight="">
    <VehicleDetails>
      <Detail name="AVC" value="1001" />
      <Detail name="LPNumber" value="MH04BY13" />
    </VehicleDetails>
  </Vehicle>
  <Payment>
    <Amount curr="INR" value="100" PriceMode="DISTANCE" IsOverWeightCharged="FALSE" PaymentMode="Tag">
      <OverwightAmount curr="INR" value="0" PaymentMode="Tag"/>
    </Amount>
  </Payment>
  <Signature>...</Signature>
</etc:ReqPay>
```

#### Field Definitions (Request)
| Field         | Description                                 | Type         | Format/Length                | Mandatory |
|---------------|---------------------------------------------|--------------|------------------------------|-----------|
| msgId         | Message identifier (unique per request)     | Alphanumeric | 1-35                         | Yes       |
| orgId         | Organization ID (assigned by acquirer)      | Alphanumeric | 4                            | Yes       |
| ts            | Request timestamp (ISO 8601)                | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| ver           | API version (should be "1.0")              | Alphanumeric | "1.0"                        | Yes       |
| Meta          | MIS/analysis info (name/value pairs)        | -            | -                            | Optional  |
| id (Txn)      | Unique transaction ID (UUID recommended)    | Alphanumeric | 1-22                         | Yes       |
| note          | Description of the transaction              | String       | 0-50                         | Optional  |
| orgTxnId      | Original transaction ID (for reversal)      | Alphanumeric | 1-36                         | Optional  |
| refId         | External reference number                   | Alphanumeric | 0-35                         | Optional  |
| refUrl        | URL for the transaction                     | String       | 0-35                         | Optional  |
| ts (Txn)      | Transaction origination time                | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| type (Txn)    | Type of transaction (DEBIT/CREDIT/NON_FIN)  | Enum         | 1-20                         | Yes       |
| id (EntryTxn) | Unique transaction ID (UUID recommended)    | Alphanumeric | 1-22                         | Yes       |
| tsRead        | Reader read time                            | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| type (EntryTxn)| Type of transaction (DEBIT/CREDIT/NON_FIN) | Enum         | 1-20                         | Yes       |
| Plaza         | Plaza info                                 | -            | -                            | Yes       |
| Lane/EntryLane| Lane info                                  | -            | -                            | Yes       |
| ReaderVerificationResult | Tag/vehicle verification info     | -            | -                            | Optional  |
| Vehicle       | Vehicle info                               | -            | -                            | Yes       |
| Payment       | Payment info                               | -            | -                            | Yes       |
| Signature     | Digital signature (placeholder for now)     | -            | -                            | Yes       |

---

### Response (Success)
```
<etc:RespPay xmlns:etc="http://npci.org/etc/schema/">
  <Head msgId="..." orgId="..." ts="YYYY-MM-DDThh:mm:ss" ver="1.0"/>
  <Meta></Meta>
  <Txn id="..." note="" orgTxnId="" refId="" refUrl="" ts="YYYY-MM-DDThh:mm:ss" type="DEBIT" txnLiability="">
    <EntryTxn id="..." tsRead="YYYY-MM-DDThh:mm:ss" ts="YYYY-MM-DDThh:mm:ss" type="DEBIT" />
  </Txn>
  <Resp plazaId="1234" respCode="00" result="ACCEPTED" ts="YYYY-MM-DDThh:mm:ss" FareType="FULL">
    <Ref TollFare="100" approvalNum="1234" errCode="000" settCurrency="INR"/>
    <Vehicle TID="..." tagId="...">
      <VehicleDetails>
        <Detail name="VEHICLECLASS" value="VC4" />
        <Detail name="REGNUMBER" value="MH04BY13" />
        <Detail name="COMVEHICLE" value="F" />
      </VehicleDetails>
    </Vehicle>
  </Resp>
  <Signature>...</Signature>
</etc:RespPay>
```

### Response (Failure)
```
<etc:RespPay xmlns:etc="http://npci.org/etc/schema/">
  <Head msgId="..." orgId="..." ts="YYYY-MM-DDThh:mm:ss" ver="1.0"/>
  <Meta></Meta>
  <Txn id="..." note="" orgTxnId="" refId="" refUrl="" ts="YYYY-MM-DDThh:mm:ss" type="DEBIT" txnLiability="">
    <EntryTxn id="..." tsRead="YYYY-MM-DDThh:mm:ss" ts="YYYY-MM-DDThh:mm:ss" type="DEBIT" />
  </Txn>
  <Resp plazaId="1234" respCode="102" result="DECLINED" ts="YYYY-MM-DDThh:mm:ss" FareType="">
    <Ref />
    <Vehicle />
  </Resp>
  <Signature>...</Signature>
</etc:RespPay>
```

#### Field Definitions (Response)
| Field         | Description                                 | Type         | Format/Length                | Mandatory |
|---------------|---------------------------------------------|--------------|------------------------------|-----------|
| msgId         | Echoed from request                         | Alphanumeric | 1-35                         | Yes       |
| orgId         | Echoed from request                         | Alphanumeric | 4                            | Yes       |
| ts            | Response timestamp (ISO 8601)               | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| ver           | API version (should be "1.0")              | Alphanumeric | "1.0"                        | Yes       |
| Meta          | Echoed from request                         | -            | -                            | Optional  |
| id (Txn)      | Transaction ID (echoed from request)        | Alphanumeric | 1-22                         | Yes       |
| note          | Description of the transaction              | String       | 0-50                         | Optional  |
| orgTxnId      | Original transaction ID (for reversal)      | Alphanumeric | 1-36                         | Optional  |
| refId         | External reference number                   | Alphanumeric | 0-35                         | Optional  |
| refUrl        | URL for the transaction                     | String       | 0-35                         | Optional  |
| ts (Txn)      | Transaction origination time                | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| type (Txn)    | Type of transaction (DEBIT/CREDIT/NON_FIN)  | Enum         | 1-20                         | Yes       |
| EntryTxn      | Entry transaction info                      | -            | -                            | Yes       |
| Resp          | Response element                            | -            | -                            | Yes       |
| plazaId       | Plaza ID                                   | Alphanumeric | 1-6                          | Yes       |
| respCode      | Response code                               | Numeric      | 3                            | Yes       |
| result        | "ACCEPTED", "DECLINED", or "INPROCESS"      | Enum         | -                            | Yes       |
| ts (Resp)     | Response timestamp (ISO 8601)               | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| FareType      | Fare type                                   | Enum         | -                            | Optional  |
| Ref           | Reference info                              | -            | -                            | Optional  |
| TollFare      | Toll fare                                   | Decimal      | 1-18                         | Optional  |
| approvalNum   | Approval number                             | Alphanumeric | 1-4                          | Optional  |
| errCode       | Error code (if any)                         | Numeric      | 3                            | Optional  |
| settCurrency  | Settlement currency                         | Alpha        | 1-3                          | Optional  |
| Vehicle       | Vehicle info                               | -            | -                            | Optional  |
| VehicleDetails| List of vehicle details                     | -            | -                            | Optional  |
| Detail        | Name/value pairs for vehicle info           | -            | -                            | Optional  |
| Signature     | Digital signature (placeholder for now)     | -            | -                            | Yes       |

---

## 6. Request Query Exception List API

### Purpose
Fetch the incremental exception list from the acquirer bank, containing the latest status of Tag IDs for specified exception types.

### Request (ReqQueryExceptionList)
```
POST <UAT/PROD URL>
Content-Type: application/xml

<etc:ReqQueryExceptionList xmlns:etc="http://npci.org/etc/schema/">
  <Head ver="1.0" ts="YYYY-MM-DDThh:mm:ss" orgId="IRBL" msgId="..." />
  <Txn id="..." note="" refId="" refUrl="" ts="YYYY-MM-DDThh:mm:ss" type="Query" orgTxnId="">
    <ExceptionList>
      <Exception excCode="01" lastFetchTime="YYYY-MM-DDThh:mm:ss" />
      <Exception excCode="02" lastFetchTime="YYYY-MM-DDThh:mm:ss" />
      <!-- More <Exception> elements as needed -->
    </ExceptionList>
  </Txn>
  <Signature>...</Signature>
</etc:ReqQueryExceptionList>
```

#### Field Definitions (Request)
| Field         | Description                                 | Type         | Format/Length                | Mandatory |
|---------------|---------------------------------------------|--------------|------------------------------|-----------|
| ver           | API version (should be "1.0")              | Alphanumeric | "1.0"                        | Yes       |
| ts            | Request timestamp (ISO 8601)                | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| orgId         | Organization ID (assigned by acquirer)      | Alphanumeric | 4                            | Yes       |
| msgId         | Message identifier (unique per request)     | Alphanumeric | 1-35                         | Yes       |
| id (Txn)      | Unique transaction ID (UUID recommended)    | Alphanumeric | 1-22                         | Yes       |
| note          | Description of the transaction              | String       | 0-50                         | Optional  |
| refId         | External reference number                   | Alphanumeric | 0-35                         | Optional  |
| refUrl        | URL for the transaction                     | String       | 0-35                         | Optional  |
| ts (Txn)      | Transaction origination time                | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| type (Txn)    | Type of transaction ("Query")              | Enum         | 1-20                         | Yes       |
| orgTxnId      | Original transaction ID (for reversal)      | Alphanumeric | 1-36                         | Optional  |
| ExceptionList | List of exception requests                  | -            | -                            | Yes       |
| Exception     | Exception request                           | -            | -                            | Yes       |
| excCode       | Exception code                              | Numeric      | 2                            | Yes       |
| lastFetchTime | Last fetch time for this exception code     | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| Signature     | Digital signature (placeholder for now)     | -            | -                            | Yes       |

---

### Response (Success)
```
<etc:RespQueryExceptionList xmlns:etc="http://npci.org/etc/schema/">
  <Head msgId="..." orgId="..." ts="YYYY-MM-DDThh:mm:ss" ver="1.0"/>
  <Txn id="..." note="" orgTxnId="" refId="" refUrl="" ts="YYYY-MM-DDThh:mm:ss" type="Query">
    <Resp msgNum="1" respCode="000" result="SUCCESS" successReqCnt="1" totReqCnt="1" totalMsg="1" totalTagsInMsg="0" totalTagsInResponse="0" ts="YYYY-MM-DDThh:mm:ss">
      <Exception desc="BLACKLIST" errCode="000" excCode="01" priority="1" result="SUCCESS" totalTag="0">
        <Tag tagId="..." op="ADD" updatedTime="YYYY-MM-DDThh:mm:ss"/>
        <Tag tagId="..." op="REMOVE" updatedTime="YYYY-MM-DDThh:mm:ss"/>
      </Exception>
      <!-- More <Exception> elements as needed -->
    </Resp>
  </Txn>
  <Signature>...</Signature>
</etc:RespQueryExceptionList>
```

### Response (Failure)
```
<etc:RespQueryExceptionList xmlns:etc="http://npci.org/etc/schema/">
  <Head msgId="..." orgId="..." ts="YYYY-MM-DDThh:mm:ss" ver="1.0"/>
  <Txn id="..." note="" orgTxnId="" refId="" refUrl="" ts="YYYY-MM-DDThh:mm:ss" type="Query">
    <Resp msgNum="1" respCode="102" result="FAILURE" successReqCnt="0" totReqCnt="0" totalMsg="1" totalTagsInMsg="0" totalTagsInResponse="0" ts="YYYY-MM-DDThh:mm:ss"/>
  </Txn>
  <Signature>...</Signature>
</etc:RespQueryExceptionList>
```

#### Field Definitions (Response)
| Field         | Description                                 | Type         | Format/Length                | Mandatory |
|---------------|---------------------------------------------|--------------|------------------------------|-----------|
| msgId         | Echoed from request                         | Alphanumeric | 1-35                         | Yes       |
| orgId         | Echoed from request                         | Alphanumeric | 4                            | Yes       |
| ts            | Response timestamp (ISO 8601)               | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| ver           | API version (should be "1.0")              | Alphanumeric | "1.0"                        | Yes       |
| id (Txn)      | Transaction ID (echoed from request)        | Alphanumeric | 1-22                         | Yes       |
| note          | Description of the transaction              | String       | 0-50                         | Optional  |
| orgTxnId      | Original transaction ID (for reversal)      | Alphanumeric | 1-36                         | Optional  |
| refId         | External reference number                   | Alphanumeric | 0-35                         | Optional  |
| refUrl        | URL for the transaction                     | String       | 0-35                         | Optional  |
| ts (Txn)      | Transaction origination time                | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| type (Txn)    | Type of transaction ("Query")              | Enum         | 1-20                         | Yes       |
| Resp          | Response element                            | -            | -                            | Yes       |
| msgNum        | Message number                              | Numeric      | 1-6                          | Yes       |
| respCode      | Response code                               | Numeric      | 3                            | Yes       |
| result        | "SUCCESS", "FAILURE", or "PARTIAL"          | Enum         | -                            | Yes       |
| successReqCnt | Number of successful requests               | Numeric      | 1-2                          | Yes       |
| totReqCnt     | Total number of requests                    | Numeric      | 1-2                          | Yes       |
| totalMsg      | Total number of messages                    | Numeric      | 1-6                          | Yes       |
| totalTagsInMsg| Total tags in this message                  | Numeric      | 1-10                         | Yes       |
| totalTagsInResponse| Total tags in response                  | Numeric      | 1-10                         | Yes       |
| ts (Resp)     | Response timestamp (ISO 8601)               | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Yes       |
| Exception     | Exception info                              | -            | -                            | Optional  |
| desc          | Description of exception code               | Alphabets    | -                            | Optional  |
| errCode       | Error code (if any)                         | Numeric      | 3                            | Optional  |
| excCode       | Exception code                              | Numeric      | 2                            | Optional  |
| priority      | Priority of exception code                  | Numeric      | 1                            | Optional  |
| totalTag      | Total tags for this exception code          | Numeric      | 1-10                         | Optional  |
| Tag           | Tag info                                   | -            | -                            | Optional  |
| tagId         | Tag ID                                     | Hexadecimal  | 20-32                        | Optional  |
| op            | Operation (ADD/REMOVE)                      | Enum         | -                            | Optional  |
| updatedTime   | Last updated time of the tag                | ISODateTime  | 19 chars, YYYY-MM-DDThh:mm:ss| Optional  |
| Signature     | Digital signature (placeholder for now)     | -            | -                            | Yes       |

---

## Additional APIs

_Describe additional APIs here as needed, following the same structure._

---

## Notes
- Replace `TBD` with actual endpoint URLs once provided by the bank.
- Ensure all timestamps are in ISO 8601 format (YYYY-MM-DDThh:mm:ss).
- Signature implementation details to be finalized with the bank. 

---

## Our API Endpoints (for Bank Integration)

| Sr.No | API Name                   | UAT Endpoint                                              | PROD Endpoint                                             | Method | Description                                 |
|-------|----------------------------|----------------------------------------------------------|-----------------------------------------------------------|--------|---------------------------------------------|
| 1     | SyncTime                   | https://fastag.onebee.in/api/bank/sync_time              | https://fastag.onebee.in/api/bank/sync_time               | POST   | Bank or system posts SyncTime requests       |
| 2     | Tag Details                | https://fastag.onebee.in/api/bank/tag_details            | https://fastag.onebee.in/api/bank/tag_details             | POST   | Fetch tag/vehicle details                   |
| 3     | Check Transaction Status   | https://fastag.onebee.in/api/bank/check_txn_status       | https://fastag.onebee.in/api/bank/check_txn_status        | POST   | Check transaction status                     |
| 4     | Toll Plaza Heart Beat      | https://fastag.onebee.in/api/bank/heartbeat              | https://fastag.onebee.in/api/bank/heartbeat               | POST   | Heartbeat/status from plaza to bank         |
| 5     | ResPay (Pay Response)      | https://fastag.onebee.in/api/bank/pay_response           | https://fastag.onebee.in/api/bank/pay_response            | POST   | Bank posts pay response to you              |
| 6     | Res Query Exception List   | https://fastag.onebee.in/api/bank/exception_response     | https://fastag.onebee.in/api/bank/exception_response      | POST   | Bank posts exception list response to you   |

> **Note:** UAT and PROD endpoints are the same for now. If you deploy to a separate UAT environment, update the UAT column accordingly. 