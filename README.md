Ceci n'est pas une pipeline
===========================

Note that this project is still under heavy development. If you have questions or want to take part, email me at nebojsa.tijanic@sbgenomics.com

The goal of the project is to create a protocol and a set of open source tools to capture and disseminate computational analyses. Our approach is to: 
 - Snapshot the software binaries and all dependencies (including the OS) into a [docker] container image. 
 - Include a thin adapter layer in these images which enables the translation between a universal tool description language (TDL) and the application software in the container and provides a common interface to any scheduler / executor running the pipeline.
 - Enable the chaining of these tool descriptors via a pipeline description language (PDL) for creation of pipelines in a functional manner to build larger reproducible units.
 - An executor implementing the protocol can then efficiently and reproducibly run the pipelines provided in PDL. After the analysis is complete, a snapshot can be created which includes the executed pipeline and all input and output data. This represents a fully reproducible analysis that anyone with access can replicate.

  [docker]: http://docker.io/
