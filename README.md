# Caida to Kathara Lab
## How to use
1. Install [Kathara](https://github.com/KatharaFramework/Kathara)
2. Clone this repository
3. Run the following command in the repository directory
```bash
python3 caida_to_kathara.py -c <caida_file> [-o <output_dir>]
```
4. The output will be in the output directory or in the `./kathara_lab` directory if not specified
5. Setup Kathara with the desired settings: `kathara settings`
6. Start the lab
```bash
kathara lstart [-d <output_dir>]
```
7. Stop the lab
```bash
kathara lclean [-d <output_dir>]
```
