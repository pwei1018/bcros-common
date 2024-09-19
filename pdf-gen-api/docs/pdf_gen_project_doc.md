# Research & Development Project - Dynamic PDF Generation

## Contributors
- Aimee Gao - BC Registries - Entities - David
- Eason Pan - BC Registries - Entities - David

## Problem Statement
There are changes happening to different filing forms each year, the downloadable and editable PDFs need to be updated at least annually. The current method is to hire contractors to update all PDFs, which cost a lot and not dynamic enough as per changes rolling out during the year.

## Reframe the Problem
How might we generate downloadable and editable PDFs dynamically when changes happen in an automated manner.

## Project Goals
- Explore possibilities and feasibility of having a piece of technology to solve this problem.
- Create Proof of Concept (POC) software to validate assumptions.
- Create pathways for future development.

## POC Description
### Stage - 1 - v.0.2
- From one page / filing, generate an editable PDF (fillable on computers) with the updated content.
- Limited to simple forms (using AGM Location change as a sample run)
### Evaluation Criteria for Potential Solutions
-	Cost of use (one-time cost, ongoing cost)
-	Alignment with current team technical expertise. (Languages, frameworks, supported database type, etc.)
-	Alignment with existing infrastructure (API endpoints, schema in database, etc.)
-	Learning curve (is it well documented, are there available learning resources)
-	Maintainability (may be considered later)
-	Evaluate the strengths and weaknesses (Trade-off) of the solutions, supported features and performance.
---
### Stage - 2 - v.0.3
- Multi-page filing PDF Form with multiple types of components
- Be able to resolve nested `$ref` in the schemas (JSON)
- Be able to render content with certain order, if a config is available
- Be able to pick up new changes in the schemas even without a proper config file
- Be able to render an instruction section at the end of the PDF
- Be able to render content dynamically(instead of hard-coded) in certain extend

## Project Timeline
### Stage 1 - Done
- Milestone 0 - Planning and kick-off: May 30, 2024 (Thur.)
- Milestone 1 - Narrow down selections (possible solutions): June 05, 2024 (Wed.)
- Milestone 2 - Come up with a package of preliminary design and POC (v.0.2) for a demo (generating an AGM Location Change Form)

### Stage 2 - In Progress
- Milestone 0 - Information gathering and analysis [Done]: 
    - Analyze the key challenges to deal with complex forms like Amalgamation Application form [Done]
    - Make decisions on the expected outcomes [Done]
- Milestone 1 - Restructure Classes [Done]: restructure each Classes adapting the challenges
- Milestone 2 - Upgrade the Infrastructure [In-Progress]:
    - Update/Add Modules [90%]
    - Update configs [99%]
    - Update Core Classes
        - Parser [Done], 
        - Coordinator[Done], 
        - Generator [10%]
        - Driver [10%]
- Milestone 4 - Craft Demos [Planned]: 
    - **Demo-1: Happy Path** - Generate an Amalgamation Application PDF **with** its configurations in pace.
        - Demonstrating the capability to render content based on its schema and configured styles, order and anything in the configurations.
        - Mimicking the scenario that everything is in place and ready to go.
    - **Demo-2: Raw but Works** - Generate an Amalgamation Application PDF **without** configurations ready
        - Demonstrating the capability to render content purely based on its schema. 
        - Mimicking the scenario that a new schema has been added, but configurations are not yet implemented
    - **Demo-3: Left Nothing** - Generate an Amalgamation Application PDF with a **not-up-to-date** configuration.
        - Demonstrating the capability to pick up new updates in the schemas
        - Mimicking the scenario that updates are made in schemas
    - **Demo-4: No Hidden Tricks (Technical Demo Only)** - Generate an Amalgamation Application PDF with one new `$ref` added to its schema.
- Milestone 5 - Future Work & Improvements
    - Future work and improvements are discussed and documented.
    - Some improvements may be able to implement after demo (this may be out of the scope for POC)

## Current Solution Stack
Core Stack --> Custom built Business schemas Parser + ReportLab Python library --> fillable PDF
### Design
(Diagram will be added after all Classes are updated)

## Decisions and Assumptions
### PDF Styles
- This is not the focus for the POC stage.
- The section order DOES NOT have to follow the [existing version ](https://www2.gov.bc.ca/assets/gov/employment-business-and-economic-development/business-management/permits-licences-and-registration/registries-forms/form_13_ltd_-_amalgamation_application.pdf), since there are sections missing in the existing version.

### Payment / Fee Information
- Not in the scope of POC stage

### Instruction Section
- Appendix style is good enough for the POC stage

## Known Issues
- The current implementation of the Schema Parser DOES NOT address the 'if-then', 'allOf' logics detailed enough. 
    - Currently, we take out everything after 'then', and ignored the if-statement.
- Less than 1% of the items in schemas DO NOT have the 'type' attribute to indicate the data type of that item.
    - Currently, we ignore that 1% since it's low-frequency and not worth putting a lot of efforts to fix them at the POC stage. So there might be some deficiencies in the final renders, but they should be minor and can almost been ignored.

## Future Work
- Design & implement the PDF generator as a back-end service and can be accessed through APIs
- Implement Business Schema update feature
    - Be able to schedule check & update job to fetch the latest business schemas from the `bcgov/business-schemas` repo and download them to this repo and update the previous ones.
    - Since the Schema Parser has been designed to pick up all new changes, the PDFs generated after the schema updates should be updated, but may not have proper configurations for styles and section order, etc.
- Fix the known issues listed above
- Optimize algorithms when needed
