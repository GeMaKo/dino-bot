def analyze_gem_direction_and_block(
    dino_pos: tuple[int, int], enemy_pos: tuple[int, int], gem_pos: tuple[int, int]
) -> dict:
    """
    Analyze relative direction of gem from dinobot and enemy,
    and whether dinobot can block the enemy by moving on the same axis and closer to the gem.
    Returns a dict with direction info and block possibility.
    """

    def direction(from_pos, to_pos):
        dx, dy = to_pos[0] - from_pos[0], to_pos[1] - from_pos[1]
        dir_x = "right" if dx > 0 else "left" if dx < 0 else "same"
        dir_y = "down" if dy > 0 else "up" if dy < 0 else "same"
        return (dir_x, dir_y)

    dino_dir = direction(dino_pos, gem_pos)
    enemy_dir = direction(enemy_pos, gem_pos)

    # Check if dino can block enemy on same axis (row or column) and closer to gem
    block_possible = False
    block_axis = None
    # Same row
    if dino_pos[1] == enemy_pos[1] == gem_pos[1]:
        if abs(dino_pos[0] - gem_pos[0]) < abs(enemy_pos[0] - gem_pos[0]):
            block_possible = True
            block_axis = "row"
    # Same column
    elif dino_pos[0] == enemy_pos[0] == gem_pos[0]:
        if abs(dino_pos[1] - gem_pos[1]) < abs(enemy_pos[1] - gem_pos[1]):
            block_possible = True
            block_axis = "column"

    return {
        "dino_to_gem_direction": dino_dir,
        "enemy_to_gem_direction": enemy_dir,
        "block_possible": block_possible,
        "block_axis": block_axis,
    }
